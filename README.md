# WNBA Box Scores (2019–2026)

Python scripts that pull every completed **WNBA regular-season** game from ESPN's public API and save the box scores as CSV files. There is one script per season, in the `Code/` folder, covering the **2019, 2020, 2021, 2022, 2023, 2024, 2025 and 2026** seasons.

## Repository layout

```
Code/
    wnba_boxscores_2019.py
    wnba_boxscores_2020.py
    wnba_boxscores_2021.py
    wnba_boxscores_2022.py
    wnba_boxscores_2023.py
    wnba_boxscores_2024.py
    wnba_boxscores_2025.py
    wnba_boxscores_2026.py
wnba_2019_csv/
    games.csv
    player_stats.csv
    team_stats.csv
wnba_2020_csv/
    ...
wnba_2021_csv/
    ...
wnba_2022_csv/
    ...
wnba_2023_csv/
    ...
wnba_2024_csv/
    ...
wnba_2025_csv/
    ...
wnba_2026_csv/
    ...
README.md
```

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

Run the script for the season you want:

```bash
python Code/wnba_boxscores_2019.py --season 2019 --out-dir wnba_2019_csv
python Code/wnba_boxscores_2020.py --season 2020 --out-dir wnba_2020_csv
python Code/wnba_boxscores_2021.py --season 2021 --out-dir wnba_2021_csv
python Code/wnba_boxscores_2022.py --season 2022 --out-dir wnba_2022_csv
python Code/wnba_boxscores_2023.py --season 2023 --out-dir wnba_2023_csv
python Code/wnba_boxscores_2024.py --season 2024 --out-dir wnba_2024_csv
python Code/wnba_boxscores_2025.py --season 2025 --out-dir wnba_2025_csv
python Code/wnba_boxscores_2026.py --season 2026 --out-dir wnba_2026_csv
```

Options:

| Flag | Description |
|------|-------------|
| `--season` | Season year to extract |
| `--out-dir` | Folder for the CSV files (use a different folder per season, or the next run overwrites the last) |
| `--workers` | Number of parallel requests (default `6`) |

## How it works

1. **Schedule:** requests ESPN's scoreboard endpoint one day at a time (Apr 15 – Oct 31 of the chosen season) and keeps only completed regular-season games. Preseason and playoff games are excluded.
2. **Box scores:** requests ESPN's summary endpoint for each game and parses game, player and team stats.
3. **Output:** writes the three CSV files. Games that fail to download are skipped and their IDs are printed at the end.

## Data source

ESPN's unofficial public API:

- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary`

This API is undocumented and may change without notice. Please use the data responsibly and respect ESPN's terms of use.
