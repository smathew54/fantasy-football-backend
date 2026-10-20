"""Season projections from prior-season performance.

The model is a formalised version of the old `top_running_backs` SQL view:
recency-weighted per-game scoring over the last few seasons, with two
additions that view lacked:

1. Seasons are also weighted by games played, so a 3-game injury year
   doesn't count as much as a full one.
2. The weighted PPG is shrunk toward the position average in proportion to
   how few games back it up ("regression to the mean"). A player with 50
   games of history keeps almost all of their own number; a player with 6
   games gets pulled a good way toward the pack.

Then an optional age adjustment, and PPG is multiplied by expected games to
get a season total. Rookies have no history and are not projected here.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ff.db import season_totals
from ff.scoring import STANDARD, ScoringSettings, score

GAMES_PER_SEASON = 17


@dataclass(frozen=True)
class ProjectionSettings:
    lookback: int = 3
    # Most recent season first. Same idea as the 1.5 / 1.25 / 1.0 in the old view.
    recency_weights: tuple[float, ...] = (1.5, 1.25, 1.0)
    # Games-equivalent worth of the position mean mixed into each player.
    # Higher = more regression to the mean.
    shrinkage_games: float = 8.0
    # Only players with at least this many games in a season contribute to
    # the position mean, so bench/injury stubs don't drag it down.
    min_games_for_mean: int = 8
    # Blend of a player's historical games/season and a full season.
    games_weight_on_history: float = 0.5
    # Per-year PPG multiplier applied for each year past the position's peak age.
    # Deliberately mild; tune against evaluate().
    age_peak: dict = field(default_factory=lambda: {"QB": 33, "RB": 26, "WR": 29, "TE": 29, "K": 40})
    age_decline_per_year: float = 0.03


def project(
    target_season: int,
    scoring: ScoringSettings = STANDARD,
    settings: ProjectionSettings = ProjectionSettings(),
    positions: list[str] | None = None,
    totals: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Project `target_season` using the `lookback` seasons before it.

    `totals` lets a caller pass pre-loaded season totals (used by evaluate()).
    """
    seasons = list(range(target_season - settings.lookback, target_season))
    if totals is None:
        totals = season_totals(seasons=seasons, positions=positions)
    else:
        totals = totals[totals["season"].isin(seasons)]
        if positions:
            totals = totals[totals["position"].isin(positions)]
    if totals.empty:
        raise ValueError(f"no season totals for {seasons}")

    totals = totals.copy()
    totals["points"] = score(totals, scoring)
    totals["ppg"] = totals["points"] / totals["games"]

    # Position mean PPG across the window, from players who actually played.
    regulars = totals[totals["games"] >= settings.min_games_for_mean]
    pos_mean = (
        regulars.groupby("position")["points"].sum()
        / regulars.groupby("position")["games"].sum()
    )

    weights = dict(zip(range(target_season - 1, target_season - settings.lookback - 1, -1),
                       settings.recency_weights))
    totals["w"] = totals["season"].map(weights)
    totals["w_games"] = totals["w"] * totals["games"]
    totals["w_points"] = totals["w"] * totals["points"]

    latest = totals.sort_values("season").groupby("player_id").last()
    g = totals.groupby("player_id")
    out = pd.DataFrame({
        "player_name": latest["player_name"],
        "position": latest["position"],
        "team": latest["team"],
        # age column is age at that season's start; roll it forward.
        "age": (latest["age"] + (target_season - latest["season"])).round(1),
        "last_season": latest["season"],
        "seasons_used": g.size(),
        "effective_games": g["w_games"].sum(),
        "weighted_ppg": g["w_points"].sum() / g["w_games"].sum(),
        "avg_games": g["games"].mean(),
    })
    # Per-season PPG for display, e.g. ppg_2024.
    per_season = totals.pivot(index="player_id", columns="season", values="ppg")
    per_season.columns = [f"ppg_{s}" for s in per_season.columns]
    out = out.join(per_season)

    k = settings.shrinkage_games
    out["pos_mean_ppg"] = out["position"].map(pos_mean)
    out["proj_ppg"] = (
        (out["effective_games"] * out["weighted_ppg"] + k * out["pos_mean_ppg"])
        / (out["effective_games"] + k)
    )

    peak = out["position"].map(settings.age_peak)
    years_past_peak = (out["age"] - peak).clip(lower=0).fillna(0)
    out["age_factor"] = (1 - settings.age_decline_per_year * years_past_peak).clip(lower=0.5)
    out["proj_ppg"] *= out["age_factor"]

    h = settings.games_weight_on_history
    out["expected_games"] = (h * out["avg_games"] + (1 - h) * GAMES_PER_SEASON).round(1)
    out["proj_points"] = (out["proj_ppg"] * out["expected_games"]).round(1)
    out["proj_ppg"] = out["proj_ppg"].round(2)

    out = out.sort_values("proj_points", ascending=False)
    out["pos_rank"] = out.groupby("position").cumcount() + 1
    out["overall_rank"] = np.arange(1, len(out) + 1)
    out.index.name = "player_id"
    return out.reset_index()


def evaluate(
    target_season: int,
    scoring: ScoringSettings = STANDARD,
    settings: ProjectionSettings = ProjectionSettings(),
    min_actual_games: int = 8,
) -> pd.DataFrame:
    """Backtest: project `target_season` from the seasons before it and compare
    to what actually happened. Returns per-position MAE and correlation of PPG.

    Only players who played `min_actual_games` in the target season are
    scored, since injuries aren't something this model tries to predict.
    """
    seasons = list(range(target_season - settings.lookback, target_season + 1))
    totals = season_totals(seasons=seasons)
    proj = project(target_season, scoring, settings, totals=totals)

    actual = totals[totals["season"] == target_season].copy()
    actual["actual_ppg"] = score(actual, scoring) / actual["games"]
    actual = actual[actual["games"] >= min_actual_games][["player_id", "actual_ppg"]]

    both = proj.merge(actual, on="player_id")
    both["err"] = both["proj_ppg"] - both["actual_ppg"]
    return (
        both.groupby("position")
        .apply(lambda d: pd.Series({
            "n": len(d),
            "mae_ppg": d["err"].abs().mean(),
            "bias_ppg": d["err"].mean(),
            "corr": d["proj_ppg"].corr(d["actual_ppg"]),
        }), include_groups=False)
        .round(3)
    )
