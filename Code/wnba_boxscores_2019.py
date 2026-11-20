#!/usr/bin/env python3
"""
Extract every WNBA 2019 regular-season box score from ESPN's public API
and write it to CSV files.

Output sheets:
  - Games         : one row per game (date, teams, score, venue, attendance)
  - Player Stats  : one row per player per game
  - Team Stats    : one row per team per game

Install:  pip install requests pandas
Run:      python wnba_boxscores_2019.py
          python wnba_boxscores_2019.py --season 2019 --out-dir wnba_2020_csv
"""

import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd
import requests

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
REGULAR_SEASON = 2  # ESPN season type: 1=preseason, 2=regular, 3=postseason

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (wnba-boxscore-extractor)"})


def get_json(url, params=None, retries=4):
    """GET with simple exponential backoff."""
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 404):
                return None  # no data for this request (e.g. off-season date)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


# --------------------------------------------------------------------------
# 1. Schedule: collect all completed regular-season event IDs
# --------------------------------------------------------------------------
def fetch_day(d):
    data = get_json(f"{BASE}/scoreboard", params={"dates": d.strftime("%Y%m%d")})
    out = {}
    for ev in (data or {}).get("events", []):
        if ev.get("season", {}).get("type") != REGULAR_SEASON:
            continue
        if not ev.get("status", {}).get("type", {}).get("completed"):
            continue
        out[ev["id"]] = ev
    return out


def fetch_schedule(year, workers=6):
    """One scoreboard request per day, Apr 15 - Oct 31 (regular season window)."""
    d, end = date(year, 4, 15), date(year, 10, 31)
    days = []
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    games = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, res in enumerate(pool.map(fetch_day, days), 1):
            games.update(res)
            if i % 40 == 0:
                print(f"  scanned {i}/{len(days)} days, {len(games)} games so far")
    print(f"Found {len(games)} completed regular-season games")
    return games


# --------------------------------------------------------------------------
# 2. Box score parsing
# --------------------------------------------------------------------------
def split_made_att(col, val):
    """'5-12' -> {'FGM': 5, 'FGA': 12} using the column label like 'FG'."""
    m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", str(val))
    if m:
        return {f"{col}M": int(m.group(1)), f"{col}A": int(m.group(2))}
    return {f"{col}M": None, f"{col}A": None}


def to_number(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return v


def parse_game(event_id, scoreboard_event):
    summary = get_json(f"{BASE}/summary", params={"event": event_id})
    if not summary:
        return None

    comp = scoreboard_event["competitions"][0]
    competitors = {c["homeAway"]: c for c in comp["competitors"]}
    home, away = competitors.get("home", {}), competitors.get("away", {})
    game_date = scoreboard_event["date"]

    game_row = {
        "GameID": event_id,
        "Date": game_date[:10],
        "Name": scoreboard_event.get("name"),
        "Away": away.get("team", {}).get("displayName"),
        "AwayScore": to_number(away.get("score")),
        "Home": home.get("team", {}).get("displayName"),
        "HomeScore": to_number(home.get("score")),
        "Venue": comp.get("venue", {}).get("fullName"),
        "Attendance": comp.get("attendance"),
        "Overtime": comp.get("status", {}).get("period", 4) > 4,
    }

    opp_lookup = {
        home.get("team", {}).get("id"): away.get("team", {}).get("displayName"),
        away.get("team", {}).get("id"): home.get("team", {}).get("displayName"),
    }
    homeaway_lookup = {
        home.get("team", {}).get("id"): "Home",
        away.get("team", {}).get("id"): "Away",
    }

    box = summary.get("boxscore", {})
    player_rows, team_rows = [], []

    # ---- player stats ----
    for team_block in box.get("players", []):
        team = team_block.get("team", {})
        tid = team.get("id")
        for stat_group in team_block.get("statistics", []):
            labels = stat_group.get("labels") or stat_group.get("names") or []
            for ath in stat_group.get("athletes", []):
                a = ath.get("athlete", {})
                row = {
                    "GameID": event_id,
                    "Date": game_date[:10],
                    "Team": team.get("displayName"),
                    "Opponent": opp_lookup.get(tid),
                    "Home/Away": homeaway_lookup.get(tid),
                    "PlayerID": a.get("id"),
                    "Player": a.get("displayName"),
                    "Position": a.get("position", {}).get("abbreviation"),
                    "Jersey": a.get("jersey"),
                    "Starter": ath.get("starter", False),
                    "DNP": ath.get("didNotPlay", False),
                    "DNPReason": ath.get("reason", ""),
                }
                stats = ath.get("stats", [])
                for label, val in zip(labels, stats):
                    if isinstance(val, str) and re.match(r"^\d+-\d+$", val.strip()):
                        row.update(split_made_att(label, val))
                    else:
                        row[label] = to_number(val)
                player_rows.append(row)

    # ---- team stats ----
    for t in box.get("teams", []):
        team = t.get("team", {})
        tid = team.get("id")
        row = {
            "GameID": event_id,
            "Date": game_date[:10],
            "Team": team.get("displayName"),
            "Opponent": opp_lookup.get(tid),
            "Home/Away": homeaway_lookup.get(tid),
        }
        for s in t.get("statistics", []):
            name = s.get("label") or s.get("name")
            val = s.get("displayValue")
            if isinstance(val, str) and re.match(r"^\d+-\d+$", val.strip()):
                row.update(split_made_att(name, val))
            else:
                row[name] = to_number(val)
        team_rows.append(row)

    return game_row, player_rows, team_rows


# --------------------------------------------------------------------------
# 3. Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2019)
    ap.add_argument("--out-dir", default="wnba_2019_csv")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    schedule = fetch_schedule(args.season, args.workers)
    if not schedule:
        sys.exit("No games found - check the season/year.")

    games, players, teams, failed = [], [], [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(parse_game, gid, ev): gid for gid, ev in schedule.items()}
        for i, fut in enumerate(as_completed(futures), 1):
            gid = futures[fut]
            try:
                res = fut.result()
                if res:
                    g, p, t = res
                    games.append(g)
                    players.extend(p)
                    teams.extend(t)
                else:
                    failed.append(gid)
            except Exception as e:  # keep going on individual failures
                print(f"  ! game {gid} failed: {e}")
                failed.append(gid)
            if i % 25 == 0 or i == len(futures):
                print(f"  processed {i}/{len(futures)}")

    games_df = pd.DataFrame(games).sort_values(["Date", "GameID"])
    players_df = pd.DataFrame(players).sort_values(["Date", "GameID", "Team"], kind="stable")
    teams_df = pd.DataFrame(teams).sort_values(["Date", "GameID"], kind="stable")

    os.makedirs(args.out_dir, exist_ok=True)
    paths = {
        "games.csv": games_df,
        "player_stats.csv": players_df,
        "team_stats.csv": teams_df,
    }
    for name, df in paths.items():
        # utf-8-sig so Excel opens accented names correctly
        df.to_csv(os.path.join(args.out_dir, name), index=False, encoding="utf-8-sig")

    print(f"\nSaved to {args.out_dir}/: {len(games_df)} games, "
          f"{len(players_df)} player rows, {len(teams_df)} team rows")
    if failed:
        print(f"Failed games ({len(failed)}): {failed}")


if __name__ == "__main__":
    main()
