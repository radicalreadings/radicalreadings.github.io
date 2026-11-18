<script setup lang="ts">
import CoverImage from '@/components/CoverImage.vue'
import QrCode from '@/components/QrCode.vue'

// Canonical URL, not window.location - so the QR is correct even if this
// page is ever loaded from localhost/preview.
const PAGE_URL = 'https://radicalreadings.github.io/mutualaid/'

// TODO: add cover images to public/covers/mutualaid/ and list them here,
// e.g. 'covers/mutualaid/first-edition.jpg'
const covers: string[] = []

// TODO: cover images for the second book, e.g. 'covers/mutualaid/second-book.jpg'
const secondCovers: string[] = []
</script>

<template>
  <v-container class="hero">
    <h1 class="hero-title">Mutual Aid Discussion</h1>
    <p class="hero-subtitle">
      <span>Reading Discussion</span>
      <span>01.12.27</span>
    </p>
  </v-container>

  <v-container class="page-section">
    <v-row>
      <v-col cols="12" md="8">
        <p class="intro-text">
          <b>Welcome to Radical Readings at Fitz.</b> Our next session will be on
          <b><em>Malcolm X Didn't Dish Out Free Bean Pies</em></b> by Kenny Lake, and <b><em>Mutual Aid</em></b> by Dean Spade.
        </p>
        <p class="intro-text">
          <b>01.12.2027</b> at <b>6PM</b> at <a href="#location" class="intro-link">Fitz</a>.
        </p>
        <p class="intro-text">
          Our discussion will focus on a
          <a href="#selected-chapters" class="intro-link">selection of chapters</a> from each book.
          [TODO: what the discussion will cover]
        </p>
      </v-col>
    </v-row>
  </v-container>

  <v-container class="page-section page-section-rule">
    <v-row>
      <!-- Mirrored layout: cover moves to the right from sm up; on phones it
           still stacks above the text like the other book. -->
      <v-col cols="12" sm="5" md="4" class="order-sm-last">
        <CoverImage :sources="secondCovers" alt="Malcolm X Didn't Dish Out Free Bean Pies - cover editions" />
      </v-col>
      <v-col cols="12" sm="7" md="8" class="chapters-col chapters-col-right">
        <div class="section-heading">
          <h2>Malcolm X Didn't Dish Out Free Bean Pies</h2>
          <p class="section-caption">by Kenny Lake</p>
        </div>
        <h3 id="selected-chapters" class="chapters-heading">Selected Chapters</h3>
        <ul class="point-list">
          <li>TODO: Chapter I - Title <i>(NN pages)</i></li>
          <li>TODO: Chapter II - Title <i>(NN pages)</i></li>
          <li>TODO: Chapter III - Title <i>(NN pages)</i></li>
        </ul>
      </v-col>
    </v-row>
  </v-container>

  <v-container class="page-section page-section-rule">
    <v-row>
      <v-col cols="12" sm="5" md="4">
        <CoverImage :sources="covers" alt="Mutual Aid - cover editions" />
      </v-col>
      <v-col cols="12" sm="7" md="8" class="chapters-col">
        <div class="section-heading">
          <h2>Mutual Aid</h2>
          <p class="section-caption">by Dean Spade</p>
        </div>
        <h3 id="selected-chapters-2" class="chapters-heading">Selected Chapters</h3>
        <ul class="point-list">
          <li>TODO: Chapter I - Title <i>(NN pages)</i></li>
          <li>TODO: Chapter II - Title <i>(NN pages)</i></li>
          <li>TODO: Chapter III - Title <i>(NN pages)</i></li>
        </ul>
        <p class="note-line">
          <span class="note-label">Note:</span>Feel free to read the whole book!<br />Our discussion
          will cover these Selected Chapters.
        </p>
      </v-col>
    </v-row>
  </v-container>

  <v-container class="page-section page-section-rule">
    <v-row align="end">
      <v-col cols="12" sm="7" md="8">
        <h2 id="location" class="section-heading">Location</h2>
        <p class="location-line"><b>Fitz Books and Waffles</b></p>
        <p class="location-line">1462 Main St. Buffalo, NY</p>
        <p class="location-line location-line-spaced"><b>6PM</b> January 12, 2027</p>
        <div class="map-embed">
          <iframe
            src="https://www.google.com/maps?q=1462+Main+St,+Buffalo,+NY&output=embed"
            title="Map showing Fitz Books and Waffles, 1462 Main St., Buffalo, NY"
            loading="lazy"
          />
        </div>
      </v-col>
      <v-col cols="12" sm="5" md="4" class="d-flex justify-sm-end">
        <QrCode :value="PAGE_URL" label="QR to this page" />
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.hero {
  padding-top: 3rem;
  padding-bottom: 1rem;
}
.hero-title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 900;
  text-transform: uppercase;
  color: rgb(var(--v-theme-primary));
  font-size: clamp(2.25rem, 7vw, 4.25rem);
  line-height: 1.02;
  letter-spacing: -0.01em;
}
.hero-subtitle {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  margin: 0.75rem 0 0;
  font-family: var(--font-label);
  font-size: clamp(1.15rem, 4vw, 1.75rem);
  color: rgba(var(--v-theme-on-background), 0.65);
}
.page-section {
  padding-top: 2rem;
  padding-bottom: 2rem;
}
.intro-text {
  margin: 0 0 1rem;
  font-size: 1.15rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-background));
}
.intro-link {
  color: rgb(var(--v-theme-primary));
  font-weight: 600;
}
.page-section-rule {
  border-top: 1px solid rgba(var(--v-theme-on-background), 0.15);
}
.section-caption {
  margin: 0 0 1rem;
  font-family: var(--font-body);
  font-size: 1.1rem;
  color: rgb(var(--v-theme-on-background));
}
.section-heading {
  margin: 0 0 1rem;
  font-family: var(--font-display);
  font-weight: 700;
  text-transform: uppercase;
  color: rgb(var(--v-theme-primary));
  font-size: 1.4rem;
}
.chapters-col {
  display: flex;
  flex-direction: column;
}
.chapters-heading {
  margin: 0 0 0.75rem;
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 900;
  font-size: 1.5rem;
}
.point-list {
  margin: 0 0 1rem;
  padding-left: 1.25rem;
  font-size: 1.15rem;
}
.point-list li {
  padding: 0.3rem 0;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}
.point-list li::marker {
  color: rgb(var(--v-theme-primary));
}
.note-line {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: auto;
  margin-bottom: 0;
  font-size: 1.05rem;
  color: rgb(var(--v-theme-on-background));
}
.location-line {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  color: rgb(var(--v-theme-on-background));
}
.location-line-spaced {
  margin-top: 0.75rem;
}
.map-embed {
  position: relative;
  width: 100%;
  aspect-ratio: 6 / 3;
  margin-top: 0.75rem;
  border: var(--border-accent);
}
.map-embed iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.note-label {
  font-weight: 600;
  white-space: nowrap;
}
/* Right-aligned book section, only once the columns sit side by side
   (Vuetify's sm breakpoint). Bullets move inside so they hug the text. */
@media (min-width: 600px) {
  .chapters-col-right {
    text-align: right;
  }
  .chapters-col-right .point-list {
    padding-left: 0;
    list-style-position: inside;
  }
  .chapters-col-right .note-line {
    justify-content: flex-end;
  }
}
</style>
