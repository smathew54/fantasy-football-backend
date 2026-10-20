"""Load player stats from nflverse into the local SQLite DB.

    python -m scripts.backfill              # every season since FIRST_SEASON
    python -m scripts.backfill 2024 2025    # just these seasons
"""
import argparse
import logging

from ff.data import available_seasons, fetch_player_weeks
from ff.db import write_player_weeks
from ff.config import DB_PATH


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seasons", nargs="*", type=int, help="seasons to load (default: all)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    seasons = args.seasons or available_seasons()
    df = fetch_player_weeks(seasons)
    n = write_player_weeks(df)
    print(f"wrote {n} player-week rows for seasons {seasons} to {DB_PATH}")


if __name__ == "__main__":
    main()
