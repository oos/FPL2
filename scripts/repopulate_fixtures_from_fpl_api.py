#!/usr/bin/env python3
"""
Fetch all fixtures for the current FPL season from the public FPL API and
repopulate the local SQLite `fixtures` table. This script:
  - Downloads teams to map team ids to names
  - Downloads all fixtures (all gameweeks)
  - DELETEs from `fixtures` (does not recreate the table)
  - INSERTs a full dataset with team NAMES and FDR values per side

Run non-interactively: python3 scripts/repopulate_fixtures_from_fpl_api.py
"""

import sys
import sqlite3
import requests
from pathlib import Path

DB_PATH = Path('fpl.db')
# Endpoints per community docs
FPL_STATIC = 'https://fantasy.premierleague.com/api/bootstrap-static/'
FPL_FIXTURES_URL = 'https://fantasy.premierleague.com/api/fixtures/'


def fetch_json(url: str):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    if not DB_PATH.exists():
        print(f'ERROR: Database not found at {DB_PATH.resolve()}')
        return 2

    print('Fetching teams from FPL API...')
    static = fetch_json(FPL_STATIC)
    teams = static.get('teams', [])
    id_to_name = {t['id']: t['name'] for t in teams}
    id_to_short = {t['id']: t['short_name'] for t in teams}
    print(f'Loaded {len(id_to_name)} teams')

    print('Fetching fixtures from FPL API...')
    fixtures = fetch_json(FPL_FIXTURES_URL)
    # Only keep fixtures with a defined event (gameweek)
    fixtures = [fx for fx in fixtures if fx.get('event') is not None]
    print(f'Loaded {len(fixtures)} fixtures with defined gameweeks')

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # Ensure table exists (do NOT recreate)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fixtures (
                id INTEGER PRIMARY KEY,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_difficulty INTEGER NOT NULL,
                away_difficulty INTEGER NOT NULL,
                gameweek INTEGER NOT NULL
            )
            """
        )
        # Delete existing rows per user instruction
        print('Clearing existing fixtures...')
        cur.execute('DELETE FROM fixtures')

        rows = []
        for fx in fixtures:
            fid = fx['id']
            gw = fx['event']
            home_id = fx['team_h']
            away_id = fx['team_a']
            home_name = id_to_name.get(home_id, str(home_id))
            away_name = id_to_name.get(away_id, str(away_id))
            home_diff = fx.get('team_h_difficulty') or 3
            away_diff = fx.get('team_a_difficulty') or 3
            rows.append((fid, home_name, away_name, home_diff, away_diff, gw))

        print(f'Inserting {len(rows)} fixtures...')
        cur.executemany(
            'INSERT OR REPLACE INTO fixtures (id, home_team, away_team, home_difficulty, away_difficulty, gameweek) VALUES (?, ?, ?, ?, ?, ?)',
            rows,
        )
        conn.commit()
        print('Done.')

    return 0


if __name__ == '__main__':
    sys.exit(main())


