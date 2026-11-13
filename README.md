# WNBA Box Scores 2026

Python script that pulls every completed **2026 WNBA regular-season** game from ESPN's public API and saves the box scores as CSV files.

## What it produces

Running the script creates a `wnba_2026_csv/` folder with three files:

| File | Contents |
|------|----------|
| `games.csv` | One row per game: date, teams, final score, venue, attendance, overtime flag |
| `player_stats.csv` | One row per player per game: starter/DNP flags and all box score stats (shooting splits are separated into made/attempted, e.g. `3PTM`, `3PTA`) |
| `team_stats.csv` | One row per team per game: team-level box score stats |

Files are saved as UTF-8 with BOM, so they open correctly in Excel.

## Setup

Requires Python 3.9+.

```bash
python -m venv WNBA
source WNBA/bin/activate
pip install requests pandas
```

## Usage

```bash
python Code/wnba_boxscores_2026.py
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--season` | `2026` | Season year to extract |
| `--out-dir` | `wnba_2026_csv` | Folder for the CSV files |
| `--workers` | `6` | Number of parallel requests |

Example:

```bash
python Code/wnba_boxscores_2026.py --season 2026 --out-dir my_output --workers 4
```

## How it works

1. **Schedule:** requests ESPN's scoreboard endpoint one day at a time (Apr 15 – Oct 31) and keeps only completed regular-season games.
2. **Box scores:** requests ESPN's summary endpoint for each game and parses game, player and team stats.
3. **Output:** writes the three CSV files. Games that fail to download are skipped and their IDs are printed at the end.

## Data source

ESPN's unofficial public API:

- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary`

This API is undocumented and may change without notice. Please use the data responsibly and respect ESPN's terms of use.
