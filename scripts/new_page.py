#!/usr/bin/env python3
"""Scaffold a new book page for Radical Readings.

Prompts for the book's basic details, then creates:

  src/pages/<Component>.vue     the page (from scripts/templates/Page.vue.tmpl)
  src/entries/<slug>.ts         entry script that mounts the page
  <slug>/index.html             HTML entry, served at /<slug>/
  public/covers/<slug>/         folder for the cover images

and registers the page in vite.config.ts and the README's Structure table.
It can also point the site root (index.html) at the new page; it asks first,
and the default is no.

Anything it doesn't ask about is placeholder text marked TODO in the generated
files. Nothing is written until you confirm the summary.

The templates live in scripts/templates/. Edit them like normal files; values
are filled in wherever a %%NAME%% placeholder appears (see build_values()).

Usage: npm run new-page   (or: python3 scripts/new_page.py)
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).resolve().parent / "templates"

SITE_URL = "https://radicalreadings.github.io"
DEFAULT_TIME = "6PM"
YOUTUBE_PLACEHOLDER = "TODO_VIDEO_ID"

PLACEHOLDER_RE = re.compile(r"%%([A-Z_]+)%%")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMPONENT_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
JS_IDENTIFIER_RE = re.compile(r"^[A-Za-z_$][\w$]*$")

# Slugs that would collide with something at the site root: Vite emits its
# bundles to /assets/, and the rest are project folders.
RESERVED_SLUGS = {"assets", "dist", "node_modules", "public", "scripts", "src"}

# The `input: { ... },` block under build.rollupOptions in vite.config.ts.
VITE_INPUT_RE = re.compile(r"(\binput:\s*\{\n)(.*?)(\n([ \t]*)\},)", re.DOTALL)
VITE_INPUT_KEY_RE = re.compile(r"""^\s*['"]?([\w$-]+)['"]?\s*:""", re.MULTILINE)


class PlanError(Exception):
    """The repo isn't in the shape this script expects; nothing was written."""


@dataclass
class Change:
    path: Path
    content: str
    note: str = ""

    @property
    def is_new(self) -> bool:
        return not self.path.exists()


# --------------------------------------------------------------------------
# Prompting


def ask(
    label: str,
    default: str | None = None,
    validate: Callable[[str], Any] | None = None,
    optional: bool = False,
) -> Any:
    """Prompt until we get a valid answer. `validate` returns the cleaned
    value or raises ValueError with a message to show."""
    hint = f" [{default}]" if default else " (optional, Enter to skip)" if optional else ""
    while True:
        answer = input(f"{label}{hint}: ").strip() or (default or "")
        if not answer:
            if optional:
                return ""
            print("  This one is required.")
            continue
        if validate is None:
            return answer
        try:
            return validate(answer)
        except ValueError as err:
            print(f"  {err}")


def confirm(label: str, default: bool) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{label} {hint} ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer y or n.")


# --------------------------------------------------------------------------
# Deriving and validating values


def title_words(title: str) -> list[str]:
    """ASCII words of a title, minus apostrophes and a leading article."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.findall(r"[A-Za-z0-9]+", re.sub(r"['’]", "", ascii_title))
    if len(words) > 1 and words[0].lower() in ("the", "a", "an"):
        words = words[1:]
    return words


def default_slug(title: str) -> str:
    return "-".join(w.lower() for w in title_words(title))


def default_component(title: str) -> str:
    name = "".join(w[0].upper() + w[1:] for w in title_words(title))
    return f"Book{name}" if name[:1].isdigit() else name


def make_slug_validator(taken_keys: set[str]) -> Callable[[str], str]:
    def validate(slug: str) -> str:
        if not SLUG_RE.match(slug):
            raise ValueError(
                "Use lowercase letters, numbers and single hyphens, e.g. 'black-reconstruction'."
            )
        if slug in RESERVED_SLUGS:
            raise ValueError(f"'{slug}' is reserved; pick another slug.")
        if slug in taken_keys:
            raise ValueError(f"vite.config.ts already has a build input named '{slug}'.")
        for path in (ROOT / slug, ROOT / "public" / slug, ROOT / "src/entries" / f"{slug}.ts"):
            if path.exists():
                raise ValueError(f"'{slug}' is already in use: {rel(path)} exists.")
        return slug

    return validate


def validate_component(name: str) -> str:
    if not COMPONENT_RE.match(name):
        raise ValueError("Use PascalCase letters and numbers, e.g. 'BlackReconstruction'.")
    path = ROOT / "src/pages" / f"{name}.vue"
    if path.exists():
        raise ValueError(f"{rel(path)} already exists.")
    return name


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError("Use YYYY-MM-DD, e.g. 2026-12-08.") from None


def parse_youtube(value: str) -> str:
    """Accept a bare video ID or any common YouTube URL; return the ID."""
    if YOUTUBE_ID_RE.match(value):
        return value
    url = urlparse(value if "://" in value else f"https://{value}")
    host = url.netloc.lower().removeprefix("www.").removeprefix("m.")
    candidate = None
    if host == "youtu.be":
        candidate = url.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "youtube-nocookie.com", "music.youtube.com"):
        parts = url.path.strip("/").split("/")
        if parts[0] == "watch":
            candidate = parse_qs(url.query).get("v", [""])[0]
        elif len(parts) >= 2 and parts[0] in ("embed", "shorts", "live", "v"):
            candidate = parts[1]
    if candidate and YOUTUBE_ID_RE.match(candidate):
        return candidate
    raise ValueError(
        "That doesn't look like a YouTube URL or 11-character video ID. "
        "Leave it blank to use a placeholder."
    )


# --------------------------------------------------------------------------
# File contents


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    unknown = sorted(set(PLACEHOLDER_RE.findall(text)) - values.keys())
    if unknown:
        raise PlanError(
            f"scripts/templates/{template} uses unknown placeholder(s): "
            + ", ".join(f"%%{name}%%" for name in unknown)
            + f". Known: {', '.join(sorted(values))}."
        )
    return PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], text)


def vite_input_keys(vite_config: str) -> set[str]:
    match = VITE_INPUT_RE.search(vite_config)
    if not match:
        raise PlanError(
            "Couldn't find the `input: { ... }` block (build.rollupOptions.input) in "
            "vite.config.ts, so the new page couldn't be registered. Nothing was written."
        )
    return set(VITE_INPUT_KEY_RE.findall(match.group(2)))


def add_vite_input(vite_config: str, slug: str) -> str:
    match = VITE_INPUT_RE.search(vite_config)
    assert match  # checked by vite_input_keys() before prompting
    body = match.group(2).rstrip()
    lines = body.splitlines()
    if lines:
        indent = re.match(r"[ \t]*", lines[-1]).group(0)
        if not body.endswith(","):
            body += ","
    else:
        indent = match.group(4) + "  "
    key = slug if JS_IDENTIFIER_RE.match(slug) else f"'{slug}'"
    entry = f"{indent}{key}: fileURLToPath(new URL('./{slug}/index.html', import.meta.url)),"
    new_body = f"{body}\n{entry}" if body else entry
    return vite_config[: match.start(2)] + new_body + vite_config[match.end(2) :]


def add_readme_row(readme: str, row: str) -> str | None:
    """Append a row to the README's Structure table (the one whose header
    starts with '| Book |'). Returns None if the table isn't found."""
    lines = readme.splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.startswith("| Book |")), None)
    if header is None:
        return None
    last = header
    while last + 1 < len(lines) and lines[last + 1].startswith("|"):
        last += 1
    if not lines[last].endswith("\n"):
        lines[last] += "\n"
    lines.insert(last + 1, row + "\n")
    return "".join(lines)


def current_redirect(root_html: str) -> str | None:
    match = re.search(r'url=(/[^"\s]*)"', root_html)
    return match.group(1) if match else None


def repoint_redirect(root_html: str, old: str, new: str) -> str | None:
    """Swap both URLs (meta refresh + fallback link). None if either is missing."""
    meta, link = f'url={old}"', f'href="{old}"'
    if meta not in root_html or link not in root_html:
        return None
    return root_html.replace(meta, f'url={new}"').replace(link, f'href="{new}"')


def build_values(
    *, title: str, full_title: str, author: str, slug: str, component: str,
    date: dt.date, time: str, youtube_id: str,
) -> dict[str, str]:
    """Everything the templates can reference as %%NAME%%. Free text is
    HTML-escaped, since it only ever lands in HTML/Vue markup. Apostrophes are
    left alone so titles stay readable; the templates only use "-quoted
    attributes."""

    def esc(text: str) -> str:
        return html.escape(text, quote=False).replace('"', "&quot;")

    return {
        "TITLE": esc(title),
        "FULL_TITLE": esc(full_title),
        "AUTHOR": esc(author),
        "SLUG": slug,
        "COMPONENT": component,
        "PAGE_URL": f"{SITE_URL}/{slug}/",
        "DATE_SHORT": f"{date:%m.%d}.{date.year % 100:02d}",  # 11.10.26
        "DATE_NUMERIC": f"{date:%m.%d.%Y}",  # 11.10.2026
        "DATE_LONG": f"{date:%B} {date.day}, {date.year}",  # November 10, 2026
        "TIME": esc(time),
        "YOUTUBE_ID": youtube_id,
    }


# --------------------------------------------------------------------------
# Main flow


def collect_answers(taken_keys: set[str]) -> dict[str, Any]:
    print("New Radical Readings page. Enter accepts the [default]; Ctrl-C quits.\n")

    title = ask("Book title, as shown in the page header (e.g. Settlers)")
    full_title = ask("Full title, with subtitle", default=title)
    author = ask("Author")
    slug = ask(
        "URL slug (the page will live at /<slug>/)",
        default=default_slug(title) or None,
        validate=make_slug_validator(taken_keys),
    )
    component = ask(
        "Vue component name",
        default=default_component(title) or None,
        validate=validate_component,
    )

    while True:
        date = ask("Meeting date (YYYY-MM-DD)", validate=parse_date)
        if date >= dt.date.today() or confirm(f"  {date} is in the past. Use it anyway?", False):
            break

    time = ask("Meeting time", default=DEFAULT_TIME)
    youtube_id = (
        ask("YouTube video URL or ID", optional=True, validate=parse_youtube)
        or YOUTUBE_PLACEHOLDER
    )

    return dict(
        title=title, full_title=full_title, author=author, slug=slug,
        component=component, date=date, time=time, youtube_id=youtube_id,
    )


def plan_changes(answers: dict[str, Any], repoint_root: bool) -> tuple[list[Change], list[str]]:
    """Work out every file's new contents up front, so a problem with one
    file stops the run before anything is written."""
    slug, component = answers["slug"], answers["component"]
    values = build_values(**answers)
    warnings: list[str] = []

    changes = [
        Change(ROOT / "src/pages" / f"{component}.vue", render("Page.vue.tmpl", values)),
        Change(ROOT / "src/entries" / f"{slug}.ts", render("entry.ts.tmpl", values)),
        Change(ROOT / slug / "index.html", render("index.html.tmpl", values)),
        Change(ROOT / "public/covers" / slug / ".gitkeep", ""),
        Change(
            ROOT / "vite.config.ts",
            add_vite_input(read("vite.config.ts"), slug),
            f"register {slug}/index.html as a build input",
        ),
    ]

    title_cell = answers["title"].replace("|", "\\|")
    row = (
        f"| {title_cell} | `{slug}/index.html` | `src/entries/{slug}.ts` "
        f"| `src/pages/{component}.vue` | `/{slug}/` |"
    )
    readme = add_readme_row(read("README.md"), row)
    if readme is None:
        warnings.append("Couldn't find the Structure table in README.md; add the page there by hand.")
    else:
        changes.append(Change(ROOT / "README.md", readme, "add to the Structure table"))

    if repoint_root:
        root_html = read("index.html")
        old = current_redirect(root_html)
        updated = repoint_redirect(root_html, old, f"/{slug}/") if old else None
        if updated is None:
            warnings.append("Couldn't find both redirect URLs in index.html; update it by hand.")
        else:
            changes.append(Change(ROOT / "index.html", updated, f"redirect site root to /{slug}/"))

    return changes, warnings


def print_summary(answers: dict[str, Any], changes: list[Change], warnings: list[str]) -> None:
    youtube = answers["youtube_id"]
    rows = [
        ("Title", answers["title"]),
        ("Full title", answers["full_title"]),
        ("Author", answers["author"]),
        ("URL", f"{SITE_URL}/{answers['slug']}/"),
        ("Component", answers["component"]),
        ("Date", f"{answers['date']:%A, %B} {answers['date'].day}, {answers['date'].year}"),
        ("Time", answers["time"]),
        ("Video", "placeholder" if youtube == YOUTUBE_PLACEHOLDER else youtube),
    ]
    print("\nSummary")
    for label, value in rows:
        print(f"  {label + ':':<12}{value}")

    creates = [c for c in changes if c.is_new]
    updates = [c for c in changes if not c.is_new]
    width = max(len(rel(c.path)) for c in updates)
    print("\nWill create:")
    for c in creates:
        print(f"  + {rel(c.path)}")
    print("Will update:")
    for c in updates:
        print(f"  ~ {rel(c.path):<{width}}  ({c.note})")
    for warning in warnings:
        print(f"\nWarning: {warning}")
    print()


def apply_changes(changes: list[Change]) -> None:
    for c in changes:
        c.path.parent.mkdir(parents=True, exist_ok=True)
        # "x" refuses to overwrite a file that appeared since we checked.
        mode = "x" if c.is_new else "w"
        with c.path.open(mode, encoding="utf-8", newline="\n") as f:
            f.write(c.content)


def print_next_steps(answers: dict[str, Any], repointed: bool, old_redirect: str | None) -> None:
    slug, component = answers["slug"], answers["component"]
    page = ROOT / "src/pages" / f"{component}.vue"
    todos = page.read_text(encoding="utf-8").count("TODO")

    steps = [
        f"Fill in the placeholders in src/pages/{component}.vue (search for TODO, {todos} found).",
        f"Add cover images to public/covers/{slug}/ and list them in the page's `covers` array.",
        f"Add a favicon at public/favi/{slug}.jpg (or change the icon link in {slug}/index.html).",
        f"Preview it: npm run dev, then open http://localhost:5173/{slug}/",
    ]
    if not repointed:
        where = f" (it currently goes to {old_redirect})" if old_redirect else ""
        steps.append(f"When the page is ready, point the redirect in index.html at /{slug}/{where}.")

    print("Done. Next:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")


def main() -> int:
    argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    ).parse_args()

    try:
        taken_keys = vite_input_keys(read("vite.config.ts"))
        old_redirect = current_redirect(read("index.html"))

        answers = collect_answers(taken_keys)
        print(
            f"\nThe site root currently redirects to {old_redirect or '(unknown)'}. If you repoint "
            "it now, it will land on\nthis placeholder page as soon as this is pushed to main."
        )
        repoint_root = confirm(f"Point the site root at /{answers['slug']}/ now?", False)

        changes, warnings = plan_changes(answers, repoint_root)
        print_summary(answers, changes, warnings)
        if not confirm("Create these files?", True):
            print("Cancelled. Nothing was written.")
            return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled. Nothing was written.")
        return 130
    except PlanError as err:
        print(f"\nError: {err}", file=sys.stderr)
        return 1

    apply_changes(changes)
    repointed = any(c.path == ROOT / "index.html" for c in changes)
    print()
    print_next_steps(answers, repointed, old_redirect)
    return 0


if __name__ == "__main__":
    sys.exit(main())
