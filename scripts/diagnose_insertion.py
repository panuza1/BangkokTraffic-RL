"""Run the Phase 3 demand sensitivity and record insertion queues by origin."""
import collections
import csv
import statistics
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import sumo
sys.path.insert(0, str(Path(sumo.__file__).parent / 'tools'))
import traci

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ET.parse(ROOT / 'sumo/case.rou.xml').getroot()
ORIGINS = {r.get('id'): r.get('edges').split()[0] for r in ROUTES.findall('route')}


def main():
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    scenarios, queues = [], []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        additional = ET.parse(ROOT / 'sumo/detectors.add.xml')
        for detector in additional.getroot():
            detector.set('file', str(tmp / 'detectors.xml'))
        additional.write(tmp / 'detectors.add.xml')
        for scale in (0.25, 0.5, 1.0):
            routes = ET.fromstring(ET.tostring(ROUTES))
            for flow in routes.findall('flow'):
                flow.set('vehsPerHour', str(float(flow.get('vehsPerHour')) * scale))
            ET.ElementTree(routes).write(tmp / 'routes.xml')
            traci.start([str(ROOT / '.venv/bin/sumo'), '-c', str(ROOT / 'sumo/case.sumocfg'),
                         '--route-files', str(tmp / 'routes.xml'),
                         '--additional-files', str(tmp / 'detectors.add.xml'),
                         '--tripinfo-output', str(tmp / 'trips.xml'),
                         '--tripinfo-output.write-undeparted', 'true',
                         '--statistic-output', str(tmp / 'stats.xml'),
                         '--summary-output', str(tmp / 'summary.xml')])
            for second in range(1, 901):
                traci.simulationStep()
                if second % 180 == 0:
                    waiting = collections.Counter(v.split('.')[0] for v in traci.simulation.getPendingVehicles())
                    for approach, edge in ORIGINS.items():
                        queues.append([scale, second, approach, edge, waiting[approach]])
            traci.close()
            stats = ET.parse(tmp / 'stats.xml').getroot()
            vehicles = stats.find('vehicles').attrib
            final = ET.parse(tmp / 'summary.xml').getroot()[-1].attrib
            trips = ET.parse(tmp / 'trips.xml').getroot().findall('tripinfo')
            completed = [float(t.get('duration')) for t in trips if float(t.get('arrival')) >= 0]
            scheduled = len(trips)
            assert scheduled == int(vehicles['loaded']) == int(vehicles['inserted']) + int(vehicles['waiting']) + int(final['discarded'])
            assert int(vehicles['inserted']) == len(completed) + int(vehicles['running'])
            assert sum(r[4] for r in queues if r[0] == scale and r[1] == 900) == int(vehicles['waiting'])
            scenarios.append([scale, vehicles['loaded'], scheduled, vehicles['inserted'], len(completed),
                              vehicles['running'], vehicles['waiting'], stats.find('teleports').get('total'),
                              final['discarded'], stats.find('safety').get('collisions'),
                              round(statistics.mean(completed), 2) if completed else ''])
    for name, header, rows in (
        ('phase3_demand_sensitivity.csv', ['demand_fraction', 'loaded', 'scheduled', 'departed', 'arrived', 'running', 'waiting_insertion', 'teleports', 'discarded', 'collisions', 'mean_completed_travel_time_s'], scenarios),
        ('phase3_insertion_by_origin.csv', ['demand_fraction', 'elapsed_s', 'approach', 'origin_edge', 'waiting_insertion'], queues),
    ):
        with (output / name).open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
    print('Wrote Phase 3 sensitivity and origin queues to results/')


if __name__ == '__main__':
    main()
