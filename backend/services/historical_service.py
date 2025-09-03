import requests
from typing import List, Dict, Any


class HistoricalService:
    """Fetches historical FPL data from open APIs and persists via db_manager."""

    def __init__(self, db_manager):
        self.db = db_manager

    def _fetch_bootstrap(self) -> Dict[str, Any]:
        resp = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        resp.raise_for_status()
        return resp.json()

    def _fetch_gw_official(self, gw: int) -> Dict[str, Any]:
        """Fetch official per-player stats for a GW via element-summary endpoints.

        We first pull the bootstrap to enumerate element IDs, then for each element
        call /api/element-summary/{id}/ and pick the matching GW entry.
        This aligns with the totals shown on the FPL site statistics table.
        """
        bs = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
        element_ids = [int(e['id']) for e in bs.get('elements', [])]
        per_player = []
        for elem_id in element_ids:
            try:
                es = requests.get(f"https://fantasy.premierleague.com/api/element-summary/{elem_id}/").json()
                h = es.get('history', [])
                # Find matching GW
                for row in h:
                    if int(row.get('round')) == gw:
                        per_player.append({'id': elem_id, 'row': row})
                        break
            except Exception:
                continue
        return {'elements': per_player}

    def _fetch_gw_fast(self, gw: int) -> Dict[str, Any]:
        resp = requests.get(f"https://fantasy.premierleague.com/api/event/{gw}/live/")
        resp.raise_for_status()
        j = resp.json() or {}
        elements = []
        for el in j.get('elements', []) or []:
            eid = int(el.get('id') or el.get('element'))
            elements.append({'id': eid, 'row': el.get('stats', {})})
        return {'elements': elements}

    def fetch_and_store_since_last_run(self, season: str = "2025/26", start_gw: int | None = None, end_gw: int | None = None, prefer_fast: bool = False) -> Dict[str, Any]:
        """
        Pulls per-element GW stats for the given season from FPL APIs. Uses last recorded
        max gameweek to avoid re-inserting. Returns a summary dict.
        """
        last_gw = self.db.get_max_recorded_gw(season)
        from_gw = start_gw if start_gw is not None else (last_gw + 1)
        if from_gw < 1:
            from_gw = 1
        to_gw = end_gw if end_gw is not None else 38

        inserted_total = 0
        gw_summaries: List[Dict[str, Any]] = []

        for gw in range(from_gw, to_gw + 1):
            try:
                if prefer_fast:
                    live = self._fetch_gw_fast(gw)
                else:
                    live = self._fetch_gw_official(gw)
            except Exception:
                break
            elements = live.get("elements", [])
            rows: List[Dict[str, Any]] = []
            for e in elements:
                elem_id = int(e.get('id'))
                r = e.get('row', {})
                # Persist full row JSON for complete data access/display later
                import json
                rows.append({
                    'fpl_element_id': elem_id,
                    'season': season,
                    'gameweek': gw,
                    'minutes': int(r.get('minutes', 0) or 0),
                    'total_points': int(r.get('total_points', 0) or 0),
                    'goals_scored': int(r.get('goals_scored', 0) or 0),
                    'assists': int(r.get('assists', 0) or 0),
                    'clean_sheets': int(r.get('clean_sheets', 0) or 0),
                    'raw_json': json.dumps(r, separators=(',', ':')),
                })
            inserted = self.db.upsert_historical_player_stats(rows)
            inserted_total += inserted
            gw_summaries.append({'gw': gw, 'inserted': inserted})

        # Log run
        self.db.record_historical_run(season)
        return {
            'season': season,
            'from_gw': from_gw,
            'to_gw': gw_summaries[-1]['gw'] if gw_summaries else last_gw,
            'inserted_total': inserted_total,
            'by_gw': gw_summaries,
            'last_run': self.db.get_last_historical_run(season),
        }


