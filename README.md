# Test suite.

## Requirements.

- Linux, macOS, or WSL.
- A C++ compiler.
- [uv](https://docs.astral.sh/uv/).

## Usage.

```bash
uv sync

# Run all methods on Kuhn poker for 1,000 iterations.
uv run src/run.py --games kuhn --iterations 1000

# Run all methods on a few games for 5,000 iterations.
uv run src/run.py --games kuhn,leduc,liars_dice_4 --iterations 5000

# Run all methods on all 24 games. For 100,000 iterations on each poker game, 10,000 on each other game.
uv run src/run.py

# Run dual simplex on a few games.
uv run src/lp.py --games kuhn,leduc

# Run rDCFR on many restart thresholds.
uv run src/run.py --games leduc,liars_dice_2x3,liars_dice_7,goofspiel_4,oshi_zumo_4,blotto_10_3 --thresholds 0.2,0.3,0.4,0.5,0.6,0.7
```
