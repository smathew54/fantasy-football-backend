"""Print season projections.

    python -m scripts.project                       # 2026, standard scoring
    python -m scripts.project --scoring ppr --pos RB WR --top 25
    python -m scripts.project --evaluate 2025       # backtest against a past season
"""
import argparse

import pandas as pd

from ff.projections import evaluate, project
from ff.scoring import PRESETS

DISPLAY = ["pos_rank", "player_name", "position", "team", "age", "seasons_used",
           "effective_games", "weighted_ppg", "proj_ppg", "expected_games", "proj_points"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--scoring", choices=PRESETS, default="standard")
    parser.add_argument("--pos", nargs="*", help="positions to include")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--evaluate", type=int, metavar="SEASON",
                        help="backtest: project SEASON from prior years and score it")
    args = parser.parse_args()
    scoring = PRESETS[args.scoring]
    pd.set_option("display.width", 200)

    if args.evaluate:
        print(f"Backtest of {args.evaluate} ({args.scoring}):")
        print(evaluate(args.evaluate, scoring))
        return

    proj = project(args.season, scoring, positions=args.pos)
    ppg_cols = sorted(c for c in proj.columns if c.startswith("ppg_"))
    print(proj.head(args.top)[DISPLAY + ppg_cols].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
