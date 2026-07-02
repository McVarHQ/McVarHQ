# Panel 4 — auto-updating RADAR + TROPHIES

GitHub activity can't live inside a static SVG, so this package regenerates
the panel **from your real stats** on a nightly GitHub Action and commits the
fresh SVG. The README just points at `panel4_radar.svg` like any other image.

## What it draws
- **L-shaped Curry-Gold panel** (locked bevel recipe: OFF=9, BEV=5, BW=18),
  bottom-right 350x350 notch left open for the `more(me)` square.
- **Prompt** `> github.exe -RADAR` — VT323 40px, black, pulsing (panel-2/3 style).
- **Radar** (left arm): COMMITS / PRS / ISSUES / REVIEWS — **ALL-TIME** totals
  (PRs/issues via direct counts; commits/reviews summed year-by-year, since
  GitHub caps `contributionsCollection` to 1-year windows). Small `ALL-TIME`
  legend in the corner. Grow-in animation.
- **Trophies** (top band): two-tone pixel cups with glint, rank letter on the
  cup, label+value on the black base plaque. Which ones show is picked by
  `TROPHIES_SHOW` in `gen_radar.py`.
- **Trophy case**: `gen_trophy_case.py` (runs in the same workflow) renders
  ALL 8 available trophies (stars/commits/prs/issues/reviews/followers/repos/
  contrib) with current values, ranks and thresholds to `trophy_case.svg` +
  `trophy_case.md` — browse it, then set `TROPHIES_SHOW` to your picks.

## Install (your profile repo, e.g. McVarHQ/McVarHQ)
1. Copy into the repo root:
   - `.github/workflows/radar.yml`
   - `scripts/gen_radar.py`, `scripts/gen_trophy_case.py`, `scripts/fonts.py`, `scripts/palette.py`
   - `fonts/Early_GameBoy.ttf`, `fonts/VT323-Regular.ttf`  ← you must add the TTFs
2. Commit. The workflow runs on push (and nightly, and via the *Run workflow*
   button under Actions). It writes/updates `panel4_radar.svg` in the repo root.
3. Reference it from README.md:
   `<p align="center"><img src="./panel4_radar.svg" width="880"></p>`
   (final assembly will interlock it with `more(me)` — later step.)

No PAT needed: the default `GITHUB_TOKEN` covers the GraphQL stats query and
the commit (workflow has `contents: write`).

## Tuning
- `CAPS` in `gen_radar.py` — what count = 100% on each radar axis.
- `THRESH` — trophy rank cutoffs per metric.
- `MOCK` — numbers used with `--mock` (preview without API).

## Local preview
```
FONT_DIR=path/to/ttfs python scripts/gen_radar.py --mock --out preview.svg
```
`--static` strips animations (for rasterizers that can't run SMIL).
