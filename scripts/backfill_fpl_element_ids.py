#!/usr/bin/env python3
"""
Backfill FPL element IDs into the local players table.

- Matches FPL bootstrap-static elements to local players using web_name/second_name
  and team short name.
- By default runs in dry-run. Use --apply to persist changes.

Usage:
  python3 scripts/backfill_fpl_element_ids.py           # dry-run report
  python3 scripts/backfill_fpl_element_ids.py --apply   # write fpl_element_id to DB
"""

import argparse
import sys
import re
import requests

sys.path.append('.')
from backend.database.manager import DatabaseManager  # noqa: E402


def normalize(s: str) -> str:
    if not s:
        return ''
    s = s.strip().lower()
    return re.sub(r'[^a-z0-9]+', '', s)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Persist changes to DB')
    args = parser.parse_args()

    db = DatabaseManager()
    players = db.get_all_players()
    teams = {t.id: t for t in db.get_all_teams()}

    # Fetch FPL bootstrap
    bs = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    elements = bs.get('elements', [])
    teams_api = {int(t['id']): t for t in bs.get('teams', [])}

    # Build lookups
    # key: (normalized_web_name, team_short) -> element_id
    key_to_id = {}
    # also index by second_name
    second_to_id = {}
    for e in elements:
        elem_id = int(e.get('id'))
        team_short = teams_api.get(int(e.get('team') or 0), {}).get('short_name', '')
        key_to_id[(normalize(e.get('web_name')), team_short)] = elem_id
        second_to_id[(normalize(e.get('second_name')), team_short)] = elem_id

    total = len(players)
    already = 0
    matched = 0
    updated = 0
    unmatched = []

    for p in players:
        if getattr(p, 'fpl_element_id', None):
            already += 1
            continue

        team_short = None
        if p.team_id and p.team_id in teams:
            team_short = teams[p.team_id].short_name
        else:
            # fallback: infer from team name if exact match exists
            for t in teams.values():
                if normalize(t.name) == normalize(p.team):
                    team_short = t.short_name
                    break
        team_short = team_short or (p.team[:3].upper() if p.team else '')

        last_token = normalize((p.name or '').split(' ')[-1])

        elem_id = None
        # Try web_name match
        elem_id = key_to_id.get((last_token, team_short))
        # Try second_name match
        if not elem_id:
            elem_id = second_to_id.get((last_token, team_short))

        if elem_id:
            matched += 1
            if args.apply:
                db.set_player_fpl_element_id(p.id, elem_id)
                updated += 1
        else:
            unmatched.append((p.id, p.name, team_short))

    print(f"Players: {total}")
    print(f"Already had fpl_element_id: {already}")
    print(f"Matched this run: {matched}")
    if args.apply:
        print(f"Rows updated: {updated}")
    else:
        print("Dry run (use --apply to persist). No rows updated.")

    if unmatched:
        print("\nUnmatched sample (first 25):")
        for row in unmatched[:25]:
            print(f"  id={row[0]} name={row[1]!r} team_short={row[2]}")


if __name__ == '__main__':
    main()


