# WNBA Box Scores (2025 & 2026)

Python scripts that pull every completed **WNBA regular-season** game from ESPN's public API and saves the box scores as CSV files. There is one script per season: `wnba_boxscores_2025.py` and `wnba_boxscores_2026.py`.

## What it produces

For each season, the script writes three CSV files:

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

Run the script for each season:

```bash
# 2026 season
python Code/wnba_boxscores_2026.py --season 2026 --out-dir wnba_2026_csv

# 2025 season
python Code/wnba_boxscores_2025.py --season 2025 --out-dir wnba_2025_csv
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--season` | `2026` | Season year to extract |
| `--out-dir` | `wnba_2026_csv` | Folder for the CSV files |
| `--workers` | `6` | Number of parallel requests |

Use a different `--out-dir` for each season, otherwise the second run overwrites the first.

## Output layout

```
wnba_2025_csv/
    games.csv
    player_stats.csv
    team_stats.csv
wnba_2026_csv/
    games.csv
    player_stats.csv
    team_stats.csv
```

## How it works

1. **Schedule:** requests ESPN's scoreboard endpoint one day at a time (Apr 15 – Oct 31 of the chosen season) and keeps only completed regular-season games. Preseason and playoff games are excluded.
2. **Box scores:** requests ESPN's summary endpoint for each game and parses game, player and team stats.
3. **Output:** writes the three CSV files. Games that fail to download are skipped and their IDs are printed at the end.

## Data source

ESPN's unofficial public API:

- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary`

This API is undocumented and may change without notice. Please use the data responsibly and respect ESPN's terms of use.
