# Benchmark 4 Market Map: standing rules

Public GitHub Pages map of the markets where Benchmark 4 (Same Market
Benchmarking) is available. Background and setup: `README.md` and
`CONTEXT_PROMPT.md`.

## Market eligibility (Ben, 2026-11-04)

Every map update applies these rules. They live in `fetch_markets()` in
`update_market_map.py`; never remove or loosen them.

- **Exclude vanity entities.** A hotel whose code ends in `_VANITY` (any case,
  e.g. `PBISIQQ_Vanity`) is the soft-brand twin of a hotel already counted.
  Counting it counts the same property twice. Filter: `h.code !~* '_vanity$'`.
- Exclude churned enterprises: `enterprise.status = TRUE`.
- Exclude the demo enterprise (`2c77d12c-4534-42d3-8cd9-e9432c3dcdd5`) and the
  Archive and Duplicates enterprises (`NOT ILIKE 'archive'`,
  `NOT ILIKE 'duplicate%'`; the real enterprise is named "Duplicates").
- Hotel must be active and not archived.
- A market needs 4 or more distinct qualifying hotels.

Any new query, script or one-off count for this map uses the same filters.

## Updating

- The script reads the v1 (old arc) database through `.env`. Access is
  read-only. Never print or commit `.env` or any credential; this repo is public.
- `main` is protected: every change goes through a PR with one approval.
  GitHub Pages redeploys on merge.
- New markets need a row in `markets_coords.csv` (msa_id, short name, lat, lng)
  or the script skips them. Commit the CSV in the same PR as `index.html`.
- Before opening the PR, list the markets added and removed with their hotel
  counts, and check why any removed market dropped (deactivated hotels, not a
  data error).
