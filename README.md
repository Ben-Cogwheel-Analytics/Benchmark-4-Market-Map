# Benchmark 4 Market Map

An interactive map showing the markets where Cogwheel Analytics' **Benchmark 4 (Same Market Benchmarking)** product is available. Hosted on GitHub Pages and linked from the Benchmark 4 marketing one-pager.

**Live site:** https://ben-cogwheel-analytics.github.io/Benchmark-4-Market-Map/

---

## Overview

The map displays a pin for each supported market. Clicking a pin shows the city and state name. An info box in the lower right shows the total market count, which updates automatically whenever markets are added or removed.

Markets are pulled directly from the Cogwheel Analytics database — any market with **4 or more active hotels** qualifies.

---

## Repo Structure

| File | Purpose |
|---|---|
| `index.html` | The map — single-file Leaflet.js page served by GitHub Pages |
| `update_market_map.py` | Run-on-demand script that queries the DB and updates the map |
| `markets_coords.csv` | Maps MSA IDs to short display names and coordinates |
| `.env.example` | Template for required environment variables (copy to `.env`) |
| `.env` | Your local DB credentials — **gitignored, never committed** |
| `.venv/` | Python virtual environment — **gitignored** |

---

## Updating the Map

Run this script when markets are added or removed in the database:

```bash
cd Benchmark-4-Market-Map
.\.venv\Scripts\python update_market_map.py
```

The script will:
1. Pull the latest `main` branch
2. Query the database for MSAs with ≥ 4 active hotels
3. Update the markets array in `index.html`
4. Open a pull request for review

Once the PR is approved and merged, GitHub Pages redeploys automatically — no manual deploy step needed.

---

## First-Time Setup

**1. Copy the env template and fill in your database credentials:**
```bash
cp .env.example .env
```

```
DB_HOST=
DB_PORT=5432
DB_NAME=
DB_USER=
DB_PASSWORD=
```

**2. Create the virtual environment and install dependencies:**
```bash
python -m venv .venv
.\.venv\Scripts\pip install psycopg2-binary python-dotenv
```

**3. Run the script:**
```bash
.\.venv\Scripts\python update_market_map.py
```

---

## Adding a New Market's Coordinates

If a market appears in the database but has no entry in `markets_coords.csv`, the script will warn you and skip it:

```
WARNING: 1 market(s) have no coordinates entry in markets_coords.csv:
  msa_id=XXXXX  name=Some City-Region, ST (Metro)  hotels=6
Add them to markets_coords.csv and re-run.
```

To fix, add one row to `markets_coords.csv`:

```csv
XXXXX,"City, ST",lat,lng
```

Standard geocoding coordinates are fine — exact city center is not required.

---

## Market Eligibility Rules

A market is shown on the map if:
- Hotel is active and not archived
- Enterprise is not Demo, Archive, or Duplicate
- The market has **≥ 4 distinct qualifying hotels**

Source logic: `cogwheel_analytics/apps/crud/msa.py`

---

## Branch Protection

The `main` branch is protected — direct pushes are blocked. All changes go through a pull request with at least 1 approval. The update script handles branch creation and PR opening automatically.

---

## Tech Stack

- [Leaflet.js 1.9.4](https://leafletjs.com/) — map rendering
- [OpenStreetMap](https://www.openstreetmap.org/) — map tiles
- [GitHub Pages](https://pages.github.com/) — hosting
- Python + psycopg2 — database query and HTML update script
