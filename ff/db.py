"""SQLite storage. One table, `player_weeks`, keyed by (player_id, season, week).

All seasons live in the same table with a `season` column, so multi-year
queries are a GROUP BY instead of a self-join per year.
"""
import sqlite3
from pathlib import Path

import pandas as pd

from ff.config import DB_PATH

TABLE = "player_weeks"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def write_player_weeks(df: pd.DataFrame, path: Path = DB_PATH) -> int:
    """Replace the rows for every season present in `df`; leave other seasons alone.

    Re-running for a season (e.g. mid-season refresh) is safe.
    """
    seasons = sorted(df["season"].unique().tolist())
    with connect(path) as con:
        exists = con.execute(
            "select 1 from sqlite_master where type='table' and name=?", (TABLE,)
        ).fetchone()
        if exists:
            con.execute(
                f"delete from {TABLE} where season in ({','.join('?' * len(seasons))})",
                seasons,
            )
        df.to_sql(TABLE, con, if_exists="append", index=False)
        con.execute(
            f"create unique index if not exists idx_{TABLE}_key "
            f"on {TABLE} (player_id, season, week)"
        )
        con.execute(f"create index if not exists idx_{TABLE}_pos on {TABLE} (position, season)")
    return len(df)


def read_player_weeks(
    seasons: list[int] | None = None,
    positions: list[str] | None = None,
    path: Path = DB_PATH,
) -> pd.DataFrame:
    clauses, params = [], []
    if seasons:
        clauses.append(f"season in ({','.join('?' * len(seasons))})")
        params += seasons
    if positions:
        clauses.append(f"position in ({','.join('?' * len(positions))})")
        params += positions
    where = f"where {' and '.join(clauses)}" if clauses else ""
    with connect(path) as con:
        return pd.read_sql(f"select * from {TABLE} {where}", con, params=params)


def season_totals(
    seasons: list[int] | None = None,
    positions: list[str] | None = None,
    path: Path = DB_PATH,
) -> pd.DataFrame:
    """Per-player season aggregates, the equivalent of the old per-year tables."""
    weeks = read_player_weeks(seasons, positions, path)
    stat_cols = weeks.columns.difference(
        ["player_id", "player_name", "position", "season", "week", "season_type",
         "team", "opponent_team", "age"]
    )
    grouped = weeks.groupby(["player_id", "season"])
    totals = grouped[list(stat_cols)].sum()
    totals["games"] = grouped.size()
    totals["player_name"] = grouped["player_name"].last()
    totals["position"] = grouped["position"].last()
    totals["team"] = grouped["team"].last()
    totals["age"] = grouped["age"].first()
    totals["ppg"] = totals["fantasy_points"] / totals["games"]
    totals["ppg_ppr"] = totals["fantasy_points_ppr"] / totals["games"]
    return totals.reset_index()
