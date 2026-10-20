import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Override with FF_DB_PATH if you want the DB somewhere else.
DB_PATH = Path(os.environ.get("FF_DB_PATH", REPO_ROOT / "data" / "stats.db"))

# Positions that score in a standard lineup. Defense is team-level and comes
# from a different nflverse table, so it's handled separately later.
FANTASY_POSITIONS = ("QB", "RB", "WR", "TE", "K")

FIRST_SEASON = 2021
