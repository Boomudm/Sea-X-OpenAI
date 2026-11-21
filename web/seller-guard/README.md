# Seller Guard

An SSD review workflow demo built with Vite, React, TypeScript, Tailwind CSS and React Router.

## Features

- Review overview with a priority donut and a confidence heatmap
- Filtered review table with search, status filters and pagination
- Review modal with evidence, confidence factors and a decision for each finding
- Listing link capture and reviewer decisions stored locally in the browser
- A listing can appear in multiple heatmap cells. The donut counts that listing once.

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by Vite.

## Production build

```bash
npm run build
npm run preview
```

The production bundle is written to `dist/`.

## Data and privacy

The SSD example cases and scores are demo data. Submitted links are recorded for evidence collection and start unscored. The demo does not fetch listing contents or call an AI service. Sources and decisions are stored in the current browser.
