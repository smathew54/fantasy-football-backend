"""League scoring settings -> fantasy points from the raw stat columns.

`score(df, settings)` works on any frame that has the STAT_COLUMNS from
ff.data (weekly rows or season totals), so the same settings drive both
historical points and projections.
"""
from dataclasses import dataclass, fields

import pandas as pd


@dataclass(frozen=True)
class ScoringSettings:
    """Points per unit of each stat. Field names match the DB columns."""
    # passing
    passing_yards: float = 0.04          # 1 pt per 25 yds
    passing_tds: float = 4.0
    passing_interceptions: float = -2.0
    passing_2pt_conversions: float = 2.0
    # rushing
    rushing_yards: float = 0.1           # 1 pt per 10 yds
    rushing_tds: float = 6.0
    rushing_2pt_conversions: float = 2.0
    # receiving
    receptions: float = 0.0              # 0 = standard, 0.5 = half PPR, 1 = PPR
    receiving_yards: float = 0.1
    receiving_tds: float = 6.0
    receiving_2pt_conversions: float = 2.0
    # misc
    fumbles_lost_total: float = -2.0    # includes return fumbles, like ESPN/Yahoo (nflverse fantasy_points excludes them)
    special_teams_tds: float = 6.0
    # kicking
    fg_made_0_19: float = 3.0
    fg_made_20_29: float = 3.0
    fg_made_30_39: float = 3.0
    fg_made_40_49: float = 4.0
    fg_made_50_59: float = 5.0
    fg_made_60_: float = 5.0
    fg_missed: float = -1.0              # derived: fg_att - fg_made
    pat_made: float = 1.0
    pat_missed: float = -1.0             # derived: pat_att - pat_made

    def with_updates(self, **changes) -> "ScoringSettings":
        return ScoringSettings(**{**self.__dict__, **changes})


STANDARD = ScoringSettings()
HALF_PPR = STANDARD.with_updates(receptions=0.5)
PPR = STANDARD.with_updates(receptions=1.0)

PRESETS = {"standard": STANDARD, "half_ppr": HALF_PPR, "ppr": PPR}

# Stats that aren't stored directly but can be derived from stored columns.
_DERIVED = {
    "fg_missed": lambda df: df["fg_att"] - df["fg_made"],
    "pat_missed": lambda df: df["pat_att"] - df["pat_made"],
}


def score(df: pd.DataFrame, settings: ScoringSettings = STANDARD) -> pd.Series:
    """Fantasy points for each row of `df` under `settings`."""
    points = pd.Series(0.0, index=df.index)
    for f in fields(settings):
        weight = getattr(settings, f.name)
        if weight == 0:
            continue
        values = _DERIVED[f.name](df) if f.name in _DERIVED else df[f.name]
        points += weight * values.fillna(0)
    return points.round(2)
