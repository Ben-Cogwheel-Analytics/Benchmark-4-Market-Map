# Context Handoff: Benchmark 4 Market Map

## What This Is
A public GitHub Pages map showing which markets have Cogwheel Analytics
Benchmark 4 (Same Market Benchmarking) coverage.

- **Repo:** https://github.com/Ben-Cogwheel-Analytics/Benchmark-4-Market-Map
- **Live site:** https://ben-cogwheel-analytics.github.io/Benchmark-4-Market-Map/
- **Working directory:** C:\Users\Benjg\dev\cogwheel\Benchmark-4-Market-Map

---

## Repo Structure

| File | Purpose |
|---|---|
| `index.html` | The map. Single-file Leaflet.js page hosted on GitHub Pages. |
| `update_market_map.py` | Run-on-demand script. Queries DB → updates index.html → commits/pushes. |
| `markets_coords.csv` | Maps MSA ID → short display name + lat/lng. Maintained manually. |
| `.env` | DB credentials. **Gitignored. Never commit.** |
| `.env.example` | Template showing required variable names (no values). |
| `.venv/` | Python virtual environment. Gitignored. |

---

## How to Run the Update Script

```
cd C:\Users\Benjg\dev\cogwheel\Benchmark-4-Market-Map
.\.venv\Scripts\python update_market_map.py
```

The script will:
1. Pull latest `main` from GitHub
2. Read DB credentials from `.env`
3. Query for MSAs with >= 4 active, non-archived, non-demo hotels
4. Match each MSA to `markets_coords.csv` using the numeric MSA ID
5. Rewrite the `var markets = [...]` array in `index.html`
6. Create a dated branch, commit, and open a PR
7. Print the PR URL — review and merge to publish

**Main branch is protected** — direct pushes are blocked. All changes
go through a PR with at least 1 approval required.

---

## When a New Market Appears With No Coordinates

The script will warn but not crash:
```
WARNING: 1 market(s) have no coordinates entry in markets_coords.csv:
  msa_id=XXXXX  name=Some City-Region, ST (Metro)  hotels=6
Add them to markets_coords.csv and re-run.
```

To fix: add one row to `markets_coords.csv`:
```
msa_id,short_name,lat,lng
XXXXX,"City, ST",lat,lng
```
Then re-run the script.

---

## Eligibility Rules (from the old-arc backend)

A market appears on the map if:
- `hotel.is_active = TRUE`
- `hotel.is_archive = FALSE` (or NULL)
- `enterprise.name NOT IN ('Archive', 'Duplicate')`
- Enterprise UUID `2c77d12c-4534-42d3-8cd9-e9432c3dcdd5` excluded (demo)
- Market has **>= 4 distinct hotels** meeting the above criteria

Source: `cogwheel_analytics/apps/crud/msa.py`

---

## Map Technical Notes

- Built with Leaflet.js 1.6.0 (same CDN as original Folium-generated version)
- One shared pin icon (base64 encoded, defined once in index.html)
- Markets defined as a plain JS array — one line per city
- Info box market count is derived from `markets.length` automatically
- Map variable: `cwMap` (not `map` — avoids browser conflicts)
- Logo: Cogwheel Analytics logo, bottom-left, z-index 999999
- Brand color: `#4B2E83`
- Info box position: lat/lng `[35.0, -75.0]` (east coast, off-shore)

---

## Branding

- **Color:** `#4B2E83`
- **Logo:** `https://cogwheelanalytics.com/assets/2024/10/Cogwheel-Analytics-Logo.webp`
- **Contact:** sales@cogwheelmarketing.com
- **Website:** www.cogwheelanalytics.com

---

## Security Notes

- `.env` is gitignored — confirmed blocked by `git check-ignore`
- This is a **public** GitHub repo (GitHub Pages requirement)
- Never hardcode credentials anywhere in the repo
- `.venv/` is also gitignored
- Leaflet loaded from unpkg with SRI integrity hashes (1.9.4)
- Popup uses `textContent` (not innerHTML) — XSS safe
- Market names are `html.escape()` + `json.dumps()` sanitised in the script
- Main branch is protected: PRs + 1 approval required before merge

---

## Current State (as of 2026-06-02)

- **45 markets** live on the map, sourced from the DB via `update_market_map.py`
- Script has been run successfully end-to-end against the production DB
- All 45 MSA IDs have coordinates in `markets_coords.csv`
