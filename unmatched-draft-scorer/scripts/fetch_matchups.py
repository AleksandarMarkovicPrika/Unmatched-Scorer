#!/usr/bin/env python3
"""Download Tabletop League's Unmatched hero-matchup CSV and publish it beside the app.

Run by .github/workflows/refresh-data.yml once a day. Needs two settings:
  TTL_API_KEY  - your personal Tabletop League API key (repo secret)
  TTL_CSV_URL  - the hero-matchups export URL from tabletopleague.com/api/reference
                 (repo variable)

The new file only replaces data/hero-matchups-unmatched.csv after it passes
validation, so a failed or odd download never breaks the live app: the last good
data stays published and the workflow run is marked as failed so you get an email.

Data: Tabletop League (tabletopleague.com). Their Terms (section 7) allow
non-commercial public use of these aggregate exports with that credit.
"""
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
CSV_PATH = os.path.join(OUT_DIR, "hero-matchups-unmatched.csv")
META_PATH = os.path.join(OUT_DIR, "meta.json")
REQUIRED = ["Hero A", "Hero B", "Hero A Win Rate %", "Games"]
MIN_ROWS = 500          # the real export has thousands; far fewer means something is wrong
MIN_HEROES = 30


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def download(url, key):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "text/csv",
        "User-Agent": "unmatched-draft-scorer (daily refresh via GitHub Actions)",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            limit = res.headers.get("X-RateLimit-Remaining")
            if limit is not None:
                print(f"Rate limit remaining: {limit}")
            return res.read().decode("utf-8-sig")
    except urllib.error.HTTPError as e:
        hint = {401: "the API key is missing, wrong or revoked",
                403: "the key is not allowed to read this export",
                404: "TTL_CSV_URL is wrong - copy it again from tabletopleague.com/api/reference",
                429: "rate limited - try again later"}.get(e.code, "")
        fail(f"Tabletop League answered HTTP {e.code}{' - ' + hint if hint else ''}.")
    except urllib.error.URLError as e:
        fail(f"Could not reach Tabletop League: {e.reason}")


def validate(text):
    if text.lstrip().startswith("<"):
        fail("Got an HTML page instead of a CSV (probably a sign-in page) - check TTL_API_KEY.")
    if text.lstrip().startswith("{"):
        fail(f"Got JSON instead of a CSV: {text[:300]}")
    rows = list(csv.DictReader(io.StringIO(text)))
    header = rows[0].keys() if rows else []
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        fail(f"CSV is missing columns {missing}. Is TTL_CSV_URL the hero *matchups* export?")
    good, heroes = 0, set()
    for r in rows:
        try:
            wr, games = float(r["Hero A Win Rate %"]), int(float(r["Games"]))
        except (TypeError, ValueError):
            continue
        if r["Hero A"] and r["Hero B"] and 0 <= wr <= 100 and games >= 0:
            good += 1
            heroes.update((r["Hero A"], r["Hero B"]))
    if good < MIN_ROWS or len(heroes) < MIN_HEROES:
        fail(f"Only {good} valid matchups / {len(heroes)} heroes - refusing to replace the published data.")
    return good, len(heroes)


def main():
    key, url = os.environ.get("TTL_API_KEY", "").strip(), os.environ.get("TTL_CSV_URL", "").strip()
    if not key:
        fail("Repository secret TTL_API_KEY is not set (Settings > Secrets and variables > Actions).")
    if not url.startswith("https://"):
        fail("Repository variable TTL_CSV_URL is not set (Settings > Secrets and variables > Actions > Variables).")

    text = download(url, key)
    rows, heroes = validate(text)

    os.makedirs(OUT_DIR, exist_ok=True)
    old = None
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            old = f.read()
    if old == text:
        print(f"No change: {rows} matchups, {heroes} heroes.")
        return
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "matchups": rows, "heroes": heroes,
                   "source": "Data: Tabletop League (tabletopleague.com)"}, f, indent=2)
    print(f"Updated: {rows} matchups, {heroes} heroes.")


if __name__ == "__main__":
    main()
