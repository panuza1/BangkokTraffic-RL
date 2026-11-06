"""Run the case in SUMO GUI and record visual and signal samples."""
import csv
import sys
from pathlib import Path
import sumo
sys.path.insert(0, str(Path(sumo.__file__).parent / 'tools'))
import traci

traci.start(['.venv/bin/sumo-gui', '-c', 'sumo/case.sumocfg', '--start', '--window-size', '1200,850', '--delay', '5', '--quit-on-end'])
try:
    traci.gui.setOffset('View #0', 310, 1125)
    traci.gui.setZoom('View #0', 700)
    tls = traci.trafficlight.getIDList()[0]
    samples = []
    for t in range(900):
        traci.simulationStep()
        if t in (59, 89, 120, 150, 200):
            ids = traci.vehicle.getIDList()
            samples.append([t+1, traci.trafficlight.getRedYellowGreenState(tls), len(ids),
                            sum(traci.vehicle.getSpeed(v) > 0.5 for v in ids)])
        if t in (89, 150):
            traci.gui.screenshot('View #0', str(Path(f'results/phase3_gui_{t+1}.png').resolve()))
    with Path('results/phase3_gui_samples.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['second', 'signal_state', 'active_vehicles', 'vehicles_over_0_5_mps'])
        writer.writerows(samples)
finally:
    traci.close()
print('GUI inspection complete; images and sampled states written to results/.')
