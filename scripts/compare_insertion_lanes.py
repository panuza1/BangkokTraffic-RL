"""Compare insertion lane choices without changing the illustrative demand or network."""
import collections
import csv
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import sumo
sys.path.insert(0, str(Path(sumo.__file__).parent / 'tools'))
import traci

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        additional = ET.parse(ROOT / 'sumo/detectors.add.xml')
        for detector in additional.getroot():
            detector.set('file', str(tmp / 'detectors.xml'))
        additional.write(tmp / 'detectors.add.xml')
        for lane_choice in ('best', 'free'):
            for scale in (0.25, 0.5, 1.0):
                routes = ET.parse(ROOT / 'sumo/case.rou.xml')
                for flow in routes.getroot().findall('flow'):
                    flow.set('departLane', lane_choice)
                    flow.set('vehsPerHour', str(float(flow.get('vehsPerHour')) * scale))
                routes.write(tmp / 'routes.xml')
                traci.start([str(ROOT / '.venv/bin/sumo'), '-c', str(ROOT / 'sumo/case.sumocfg'),
                             '--route-files', str(tmp / 'routes.xml'),
                             '--additional-files', str(tmp / 'detectors.add.xml'),
                             '--tripinfo-output', str(tmp / 'trips.xml'),
                             '--tripinfo-output.write-undeparted', 'true',
                             '--statistic-output', str(tmp / 'stats.xml'),
                             '--summary-output', str(tmp / 'summary.xml')])
                halted = collections.Counter()
                edges = [edge for edge in traci.edge.getIDList() if not edge.startswith(':')]
                for second in range(1, 901):
                    traci.simulationStep()
                    if second % 10 == 0:
                        for edge in edges:
                            halted[edge] += traci.edge.getLastStepHaltingNumber(edge)
                pending = collections.Counter(v.split('.')[0] for v in traci.simulation.getPendingVehicles())
                traci.close()
                stats = ET.parse(tmp / 'stats.xml').getroot()
                vehicles = stats.find('vehicles').attrib
                trips = ET.parse(tmp / 'trips.xml').getroot().findall('tripinfo')
                arrived = sum(float(t.get('arrival')) >= 0 for t in trips)
                discarded = int(ET.parse(tmp / 'summary.xml').getroot()[-1].get('discarded'))
                assert len(trips) == int(vehicles['loaded']) == int(vehicles['inserted']) + int(vehicles['waiting']) + discarded
                assert int(vehicles['inserted']) == arrived + int(vehicles['running'])
                assert sum(pending.values()) == int(vehicles['waiting'])
                top = halted.most_common(1)[0] if halted else ('', 0)
                results.append([lane_choice, scale, vehicles['loaded'], vehicles['inserted'], arrived,
                                vehicles['running'], vehicles['waiting'], *(pending[f'Link{i}'] for i in (1, 3, 5, 6)),
                                stats.find('teleports').get('total'), discarded, stats.find('safety').get('collisions'),
                                top[0], top[1]])
    with (ROOT / 'results/phase3_lane_comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['depart_lane', 'demand_fraction', 'loaded', 'departed', 'arrived', 'running',
                         'waiting_insertion', 'pending_link1', 'pending_link3', 'pending_link5', 'pending_link6',
                         'teleports', 'discarded', 'collisions', 'top_halted_edge', 'halted_vehicle_samples'])
        writer.writerows(results)
    print('Wrote results/phase3_lane_comparison.csv')


if __name__ == '__main__':
    main()
