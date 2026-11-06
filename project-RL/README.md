# BangkokTraffic-RL

Research project for evaluating traffic-signal controllers in SUMO using historical Bangkok traffic observations. This is simulation-only; no real traffic infrastructure is controlled. The data audit and calibration gates in [PLAN.md](PLAN.md) must pass before training or making research claims.

## Setup and smoke test

On Ubuntu with Python 3.10 and the `venv` module available:

```sh
python3 -m venv .venv
. .venv/bin/activate
unset PYTHONPATH  # prevent an existing Python path from leaking into the virtual environment
python -m pip install -r requirements.txt
python scripts/smoke.py
```

The commands were verified with Python 3.10.12 and SUMO 1.28.0 on Ubuntu 22.04.5 x86_64. They do not establish compatibility with future simulation dependencies.

The smoke test checks that Python and the `sumo` executable run; it does not validate a traffic model. See [progress.md](progress.md) for actual environment versions and gate results.

## Reproducibility and artifacts

Record explicit integer seeds in each future experiment configuration and pass the same seeds to all relevant random generators and SUMO. Use paired seeds across controllers and keep training and held-out days separate. No experiment seeds or results have been chosen yet.

Keep source data in `data/raw/` and generated data in `data/processed/` (both ignored by Git). Place small reports in `docs/`, experiment settings in `configs/`, SUMO artifacts in `sumo/`, and small metrics and plots in `results/` as those phases require them. Do not commit large or ambiguously licensed raw data.

## Exploratory SUMO case

The current OSM-derived passenger-vehicle case is **not calibrated**. See [the Phase 3 report](docs/calibration.md) for road and signal limitations, observed-versus-simulated counts, and the substantial queue waiting to enter the model. [SUMO setup and reproduction](sumo/README.md) includes OpenStreetMap attribution and commands. Do not use the model to control real traffic or draw validated performance conclusions.
