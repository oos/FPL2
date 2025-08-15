#!/usr/bin/env python3
import os
import sys
import time
import urllib.parse
import requests

"""
Download Premier League team logos into backend/static/assets/teams.
This uses a best-effort set of Wikipedia URL patterns. Existing files are skipped.
"""

TEAMS = {
    'Arsenal': 'ARS', 'Aston Villa': 'AVL', 'Bournemouth': 'BOU', 'Brentford': 'BRE', 'Brighton': 'BHA',
    'Chelsea': 'CHE', 'Crystal Palace': 'CRY', 'Everton': 'EVE', 'Fulham': 'FUL', 'Ipswich': 'IPS',
    'Leicester': 'LEI', 'Liverpool': 'LIV', 'Man City': 'MCI', 'Man Utd': 'MUN', 'Newcastle': 'NEW',
    'Nottingham Forest': 'NFO', 'Southampton': 'SOU', 'Spurs': 'TOT', 'West Ham': 'WHU', 'Wolves': 'WOL'
}

SEARCH_CANDIDATES = [
    'https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/{name}_F.C._logo.svg/512px-{name}_F.C._logo.svg.png',
    'https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/{name}_F.C._crest.svg/512px-{name}_F.C._crest.svg.png',
    'https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/{name}_F.C._badge.svg/512px-{name}_F.C._badge.svg.png',
]

def sanitize(s: str) -> str:
    return s.replace(' ', '_')

def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def try_download(url: str, dest_path: str) -> bool:
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and resp.content:
            with open(dest_path, 'wb') as f:
                f.write(resp.content)
            return True
    except Exception:
        return False
    return False

def main():
    root = os.path.dirname(os.path.dirname(__file__))
    assets_dir = os.path.join(root, 'backend', 'static', 'assets', 'teams')
    ensure_dir(assets_dir)

    for team_name, short in TEAMS.items():
        base_file = os.path.join(assets_dir, f"{short.lower()}.png")
        if os.path.exists(base_file):
            print(f"Skipping {team_name}: already exists")
            continue

        name_token = sanitize(team_name)
        downloaded = False
        for tmpl in SEARCH_CANDIDATES:
            url = tmpl.format(name=urllib.parse.quote(name_token))
            print(f"Trying {team_name} -> {url}")
            if try_download(url, base_file):
                print(f"Downloaded logo for {team_name} -> {base_file}")
                downloaded = True
                break
            time.sleep(0.5)

        if not downloaded:
            print(f"WARNING: Could not download logo for {team_name}")

if __name__ == '__main__':
    sys.exit(main())


