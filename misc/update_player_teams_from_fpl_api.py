#!/usr/bin/env python3
"""
Update player team names and team_id using the open FPL API (bootstrap-static).

This script will:
- Fetch official teams and players from the FPL API
- Upsert teams into the local `teams` table
- Update local `players` rows with correct `team` and `team_id` via name matching

Run:
  python3 misc/update_player_teams_from_fpl_api.py
"""

import json
import re
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime
from urllib.request import urlopen, Request

DB_PATH = 'fpl.db'
FPL_BOOTSTRAP_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'


def fetch_bootstrap() -> dict:
    req = Request(FPL_BOOTSTRAP_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def normalize_name(name: str) -> str:
    if not name:
        return ''
    # strip accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    # remove dots and non-letters
    name = re.sub(r'[^a-zA-Z\s-]', '', name)
    # collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def first_initial(name: str) -> str:
    name = normalize_name(name)
    return name[0] if name else ''


def split_name_parts(full_name: str):
    full = normalize_name(full_name)
    parts = full.split(' ') if full else []
    if not parts:
        return ('', '')
    if len(parts) == 1:
        return ('', parts[0])
    return (parts[0], parts[-1])  # first, last


def upsert_teams(conn: sqlite3.Connection, teams: list[dict]) -> None:
    cur = conn.cursor()
    for t in teams:
        cur.execute(
            """
            INSERT OR REPLACE INTO teams (id, name, short_name, code, strength, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                t.get('id'), t.get('name'), t.get('short_name'), t.get('code'),
                t.get('strength', 0), datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            ),
        )
    conn.commit()


def build_api_player_index(api_players: list[dict]) -> dict:
    """Build indices to help match: by web_name, by last name + first initial."""
    by_web = {}
    by_last_initial = {}
    for p in api_players:
        first = p.get('first_name', '')
        second = p.get('second_name', '')
        web = p.get('web_name', '')
        full = f"{first} {second}".strip()

        web_n = normalize_name(web)
        if web_n:
            by_web.setdefault(web_n, []).append(p)

        _, last = split_name_parts(full)
        fi = first_initial(first)
        key = f"{last}:{fi}"
        if last:
            by_last_initial.setdefault(key, []).append(p)
    return {'by_web': by_web, 'by_last_initial': by_last_initial}


def match_player(api_index: dict, local_name: str) -> dict | None:
    """Heuristic matching: try web_name, then last name + first initial, then last name only."""
    if not local_name:
        return None
    # Try direct web_name match by last token and raw normalized full name
    web_n = normalize_name(local_name.replace('.', ' ').split()[-1])
    candidates = api_index['by_web'].get(web_n)
    if candidates:
        return candidates[0]

    full_web = normalize_name(local_name)
    candidates = api_index['by_web'].get(full_web)
    if candidates:
        return candidates[0]

    # Try last name + first initial
    first, last = split_name_parts(local_name)
    fi = first_initial(first)
    key = f"{last}:{fi}"
    candidates = api_index['by_last_initial'].get(key)
    if candidates:
        return candidates[0]

    # Try last name only
    candidates = api_index['by_web'].get(normalize_name(last))
    if candidates:
        return candidates[0]

    return None


def update_player_teams(conn: sqlite3.Connection, api_payload: dict) -> tuple[int, int]:
    teams = api_payload.get('teams', [])
    elements = api_payload.get('elements', [])

    team_by_id = {t['id']: t for t in teams}
    api_index = build_api_player_index(elements)

    cur = conn.cursor()
    cur.execute("SELECT id, name FROM players")
    players = cur.fetchall()

    updated = 0
    unmatched = 0
    for row in players:
        pid, name = row['id'], row['name']
        api_player = match_player(api_index, name)
        if not api_player:
            unmatched += 1
            continue
        team_id = api_player.get('team')
        team = team_by_id.get(team_id)
        if not team:
            unmatched += 1
            continue
        team_name = team.get('name')
        # Update DB
        cur.execute(
            "UPDATE players SET team = ?, team_id = ? WHERE id = ?",
            (team_name, team_id, pid),
        )
        updated += 1

    conn.commit()
    return updated, unmatched


def main():
    print("Fetching FPL bootstrap-static data…")
    payload = fetch_bootstrap()
    print("Fetched.")

    print("Opening database…")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        print("Upserting teams…")
        upsert_teams(conn, payload.get('teams', []))
        print("Teams updated.")

        print("Updating player team mappings…")
        updated, unmatched = update_player_teams(conn, payload)
        print(f"Player teams updated: {updated}; Unmatched: {unmatched}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()


