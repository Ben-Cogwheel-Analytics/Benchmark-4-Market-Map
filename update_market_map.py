"""
update_market_map.py

Run this script on demand to pull active Benchmark 4 markets from the
database and update the market map.

Setup:
    1. Copy .env.example to .env and fill in your DB credentials.
    2. pip install psycopg2-binary python-dotenv
    3. .\.venv\Scripts\python update_market_map.py

The script will:
    - Pull latest main from GitHub
    - Query the DB for MSAs with >= 4 active hotels
    - Match each MSA to a coordinate in markets_coords.csv
    - Rewrite the markets array in index.html
    - Open a PR for review (GitHub Pages redeploys on merge)
"""

import csv
import html as html_lib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

SCRIPT_DIR   = Path(__file__).parent
HTML_FILE    = SCRIPT_DIR / "index.html"
COORDS_FILE  = SCRIPT_DIR / "markets_coords.csv"
MIN_HOTELS   = 4
DEMO_ENTERPRISE_ID = "2c77d12c-4534-42d3-8cd9-e9432c3dcdd5"


def load_coords() -> dict:
    """Load MSA ID -> (short_name, lat, lng) from the CSV."""
    coords = {}
    with open(COORDS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            coords[row["msa_id"]] = (row["short_name"], float(row["lat"]), float(row["lng"]))
    return coords


def fetch_markets(conn) -> list[dict]:
    """Return MSAs with >= MIN_HOTELS active, non-demo hotels."""
    query = """
        SELECT
            m.msa_id,
            m.name,
            COUNT(DISTINCT h.id) AS hotel_count
        FROM msa m
        JOIN msa_zip_mapping mzm  ON mzm.msa_id    = m.id
        JOIN hotel h              ON h.zip          = mzm.zip_code
        JOIN hotel_enterprise_link hel ON hel.hotel_id = h.id
        JOIN enterprise e         ON e.id           = hel.enterprise_id
        WHERE h.is_active = TRUE
          AND COALESCE(h.is_archive, FALSE) = FALSE
          AND e.id::text   <> %s
          AND e.name NOT IN ('Archive', 'Duplicate')
        GROUP BY m.msa_id, m.name
        HAVING COUNT(DISTINCT h.id) >= %s
        ORDER BY hotel_count DESC;
    """
    with conn.cursor() as cur:
        cur.execute(query, (DEMO_ENTERPRISE_ID, MIN_HOTELS))
        rows = cur.fetchall()
    return [{"msa_id": r[0], "name": r[1], "hotel_count": r[2]} for r in rows]


def build_markets_js(markets: list[dict], coords: dict) -> tuple[str, list, list]:
    """
    Build the JavaScript markets array string.
    Returns (js_array_string, skipped_markets, included_markets).
    """
    skipped = []
    included = []
    lines = []

    for m in markets:
        msa_id = m["msa_id"]
        if msa_id not in coords:
            skipped.append(m)
            continue
        short_name, lat, lng = coords[msa_id]
        safe_name = json.dumps(html_lib.escape(short_name))
        lines.append(f'            [{safe_name}, {lat}, {lng}]')
        included.append(short_name)

    js = "        var markets = [\n"
    js += ",\n".join(lines) + "\n"
    js += "        ];"
    return js, skipped, included


def update_html(new_markets_js: str) -> bool:
    """Replace the markets array in index.html. Returns True if changed."""
    html = HTML_FILE.read_text(encoding="utf-8")

    pattern = r"        var markets = \[[\s\S]*?\];"
    if not re.search(pattern, html):
        print("ERROR: Could not find the markets array in index.html.")
        sys.exit(1)

    new_html = re.sub(pattern, new_markets_js, html)

    if new_html == html:
        return False

    HTML_FILE.write_text(new_html, encoding="utf-8")
    return True


def sync_main():
    """Pull latest main before making changes."""
    for cmd in [["git", "checkout", "main"], ["git", "pull", "origin", "main"]]:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR syncing main:\n{result.stderr}")
            sys.exit(1)


def open_pr(count: int):
    """Create a branch, commit, push, and open a PR for review."""
    branch = f"map-update-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
    steps = [
        ["git", "checkout", "-b", branch],
        ["git", "add", "index.html"],
        ["git", "commit", "-m", f"Update market map to {count} markets (automated)"],
        ["git", "push", "origin", branch],
        ["gh", "pr", "create",
         "--title", f"Market map update: {count} markets",
         "--body", (
             f"Automated update from `update_market_map.py`.\n\n"
             f"**Markets on map:** {count}\n\n"
             "Please verify the live preview looks correct before merging. "
             "GitHub Pages redeploys automatically on merge to main."
         ),
         "--base", "main"],
    ]
    for cmd in steps:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr.strip()}")
            sys.exit(1)
        if result.stdout.strip():
            print(result.stdout.strip())


def main():
    load_dotenv(SCRIPT_DIR / ".env")

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    print("Syncing with main branch...")
    sync_main()

    print("Connecting to database...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    print("Loading coordinates...")
    coords = load_coords()

    print("Fetching markets from DB...")
    markets = fetch_markets(conn)
    conn.close()

    print(f"  {len(markets)} markets qualify (>= {MIN_HOTELS} hotels)")

    new_js, skipped, included = build_markets_js(markets, coords)

    if skipped:
        print(f"\nWARNING: {len(skipped)} market(s) have no coordinates entry in markets_coords.csv and will be skipped:")
        for m in skipped:
            print(f"  msa_id={m['msa_id']}  name={m['name']}  hotels={m['hotel_count']}")
        print("Add them to markets_coords.csv and re-run.\n")

    changed = update_html(new_js)

    if not changed:
        print("No changes — map is already up to date.")
        return

    print(f"\nMap updated: {len(included)} markets")
    print("Opening PR for review...")
    open_pr(len(included))

    print(f"\nDone. PR opened — merge it to publish the map.")
    print(f"Final market count: {len(included)}")
    if skipped:
        print(f"Skipped (no coordinates): {len(skipped)}")


if __name__ == "__main__":
    main()
