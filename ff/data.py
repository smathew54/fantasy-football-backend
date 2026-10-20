"""Pull player stats from nflverse (via nflreadpy) into tidy pandas frames.

nflverse publishes weekly, per-player stats with stable IDs, so there is no
HTML to scrape and no bot blocking to work around.
"""
import logging

import nflreadpy as nfl
import pandas as pd

from ff.config import FANTASY_POSITIONS, FIRST_SEASON

log = logging.getLogger(__name__)

# Columns we keep from the ~150 nflverse provides. Everything needed for
# custom scoring, plus the pre-computed standard/PPR totals as a sanity check.
STAT_COLUMNS = [
    "completions", "attempts", "passing_yards", "passing_tds",
    "passing_interceptions", "passing_2pt_conversions",
    "carries", "rushing_yards", "rushing_tds", "rushing_2pt_conversions",
    "targets", "receptions", "receiving_yards", "receiving_tds",
    "receiving_2pt_conversions",
    "fumbles_lost_total", "special_teams_tds",
    "fg_made", "fg_att", "fg_made_0_19", "fg_made_20_29", "fg_made_30_39",
    "fg_made_40_49", "fg_made_50_59", "fg_made_60_", "pat_made", "pat_att",
    "fantasy_points", "fantasy_points_ppr",
]

KEY_COLUMNS = [
    "player_id", "player_name", "position", "season", "week", "season_type",
    "team", "opponent_team",
]


def available_seasons() -> list[int]:
    """FIRST_SEASON through the current season."""
    return list(range(FIRST_SEASON, nfl.get_current_season() + 1))


def fetch_player_weeks(seasons: list[int] | int | None = None) -> pd.DataFrame:
    """One row per player per game, fantasy positions only, regular season."""
    if seasons is None:
        seasons = available_seasons()
    log.info("fetching player stats for %s", seasons)

    stats = nfl.load_player_stats(seasons, summary_level="week").to_pandas()
    # nflverse has both a short player_name ("L.Jackson") and a display name; keep the full one.
    stats = stats.drop(columns="player_name").rename(columns={"player_display_name": "player_name"})
    stats = stats[stats["position"].isin(FANTASY_POSITIONS)]
    stats = stats[stats["season_type"] == "REG"]

    stats = stats[KEY_COLUMNS + STAT_COLUMNS].copy()
    stats[STAT_COLUMNS] = stats[STAT_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0)

    # Age matters for projections; birth_date lives in the players table.
    players = nfl.load_players().to_pandas()[["gsis_id", "birth_date"]]
    players = players.rename(columns={"gsis_id": "player_id"})
    players["birth_date"] = pd.to_datetime(players["birth_date"], errors="coerce")
    stats = stats.merge(players, on="player_id", how="left")
    season_start = pd.to_datetime(stats["season"].astype(str) + "-09-01")
    stats["age"] = ((season_start - stats["birth_date"]).dt.days / 365.25).round(1)
    stats = stats.drop(columns="birth_date")

    return stats.sort_values(["season", "week", "player_id"]).reset_index(drop=True)
