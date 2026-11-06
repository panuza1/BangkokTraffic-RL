# Sathorn–Surasak SUMO case

This is a simulation-only, uncalibrated exploratory model. Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The pinned `sathorn.osm.xml` is an unmodified extract downloaded on 2026-11-06 from `https://api.openstreetmap.org/api/0.6/map?bbox=100.5175,13.7175,100.5215,13.7205`, SHA-256 `041688bf7e1d64104c6f4a7da2540adf2a05eb3d934917606d29f8965fb42890`. OSM is current mapping, not verified 2016 geometry. The derived network and any public reuse remain subject to ODbL attribution and applicable share-alike obligations. The source observations are the Figshare dataset credited in [data/README.md](../data/README.md), CC BY 4.0.

## Reproduce

From the project root, after the documented virtual environment setup and extracting the June 2 files in [data/README.md](../data/README.md):

```sh
unset PYTHONPATH
.venv/bin/python scripts/prepare_case.py
.venv/bin/netconvert --osm-files sumo/sathorn.osm.xml --lefthand \
  --keep-edges.in-geo-boundary 100.5186,13.7178,100.5208,13.7198 \
  --keep-edges.by-vclass passenger --tls.guess-signals --tls.join \
  --tls.yellow.time 4 --tls.allred.time 2 --output-file sumo/sathorn.net.xml 2>sumo/netconvert.log
.venv/bin/python scripts/build_phase3.py
.venv/bin/python scripts/check_phase3.py
.venv/bin/sumo -c sumo/case.sumocfg 2>results/phase3_sumo.log
.venv/bin/python scripts/summarize_phase3.py
.venv/bin/python -m unittest discover -s tests -v
```

To view the run in a graphical session: `.venv/bin/sumo-gui -c sumo/case.sumocfg --start --delay 20`. Or run `.venv/bin/python scripts/inspect_phase3_gui.py` with a working `DISPLAY` to reproduce sampled signal states and screenshots. Both GUI commands run the full case and write simulation outputs under `results/`.

`netconvert.log` records import warnings, including a turn restriction for a via node outside the kept boundary and discarded public-transport elements; see [the Phase 3 report](../docs/calibration.md). The SUMO XML header contains generation timestamps, so compare parsed simulation data rather than file bytes for repeatability. This network contains no modeled pedestrians or bicycles and must not be used as a real traffic-signal design.
