"""Run controlled, temporary Phase 3 interventions and record lane queues."""
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
from check_phase3 import check_network

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / 'sumo/sathorn.net.xml'
ROUTES = ROOT / 'sumo/case.rou.xml'
ORIGINS = {'Link1': '747478914#3', 'Link3': '295789573#0',
           'Link5': '1024938013#0', 'Link6': '39943703#7'}
CASES = ('baseline', 'link3_free_lane', 'link6_storage', 'longer_greens')


def prepare(case, scale, directory):
    net = ET.parse(NETWORK)
    routes = ET.parse(ROUTES)
    if case == 'link3_free_lane':
        routes.getroot().find("flow[@id='Link3']").set('departLane', 'free')
    elif case == 'link6_storage':
        edge = net.getroot().find("edge[@id='39943703#7']")
        for lane in edge.findall('lane'):
            lane.set('length', str(float(lane.get('length')) + 100))
    elif case == 'longer_greens':
        for phase in net.getroot().find('tlLogic').findall('phase')[::3]:
            phase.set('duration', '18')
    elif case != 'baseline':
        raise ValueError(case)
    check_network(net.getroot())
    for flow in routes.getroot().findall('flow'):
        flow.set('vehsPerHour', str(float(flow.get('vehsPerHour')) * scale))
    net.write(directory / 'network.xml')
    routes.write(directory / 'routes.xml')


def write_csv(path, header, rows):
    with path.open('w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)


def main():
    results, lanes = [], []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        additional = ET.parse(ROOT / 'sumo/detectors.add.xml')
        for detector in additional.getroot():
            detector.set('file', str(tmp / 'detectors.xml'))
        additional.write(tmp / 'detectors.add.xml')
        for case in CASES:
            for scale in (0.25, 0.5, 1.0):
                prepare(case, scale, tmp)
                traci.start([str(ROOT / '.venv/bin/sumo'), '-c', str(ROOT / 'sumo/case.sumocfg'),
                             '--net-file', str(tmp / 'network.xml'), '--route-files', str(tmp / 'routes.xml'),
                             '--additional-files', str(tmp / 'detectors.add.xml'),
                             '--tripinfo-output', str(tmp / 'trips.xml'), '--tripinfo-output.write-undeparted', 'true',
                             '--statistic-output', str(tmp / 'stats.xml'), '--summary-output', str(tmp / 'summary.xml')])
                monitored = {r.get('id'): r.get('edges').split()[:-1] for r in ET.parse(ROUTES).getroot().findall('route')}
                lane_ids = {edge: traci.edge.getLaneNumber(edge) for edges in monitored.values() for edge in edges}
                counts = collections.Counter()
                maxima = collections.Counter()
                total_halted = []
                for second in range(1, 901):
                    traci.simulationStep()
                    if second % 10 == 0:
                        total = 0
                        for edge, n in lane_ids.items():
                            for i in range(n):
                                lane = f'{edge}_{i}'
                                halted = traci.lane.getLastStepHaltingNumber(lane)
                                counts[lane] += halted
                                maxima[lane] = max(maxima[lane], halted)
                                total += halted
                        total_halted.append(total)
                pending = collections.Counter(v.split('.')[0] for v in traci.simulation.getPendingVehicles())
                traci.close()
                stats = ET.parse(tmp / 'stats.xml').getroot()
                v = stats.find('vehicles').attrib
                trips = ET.parse(tmp / 'trips.xml').getroot().findall('tripinfo')
                completed = [float(t.get('duration')) for t in trips if float(t.get('arrival')) >= 0]
                discarded = int(ET.parse(tmp / 'summary.xml').getroot()[-1].get('discarded'))
                assert len(trips) == int(v['loaded']) == int(v['inserted']) + int(v['waiting']) + discarded
                assert int(v['inserted']) == len(completed) + int(v['running'])
                assert sum(pending.values()) == int(v['waiting'])
                safety, teleports = int(stats.find('safety').get('collisions')), int(stats.find('teleports').get('total'))
                results.append([case, scale, v['loaded'], v['inserted'], len(completed), v['running'], v['waiting'],
                                round(statistics.mean(total_halted), 2), max(total_halted),
                                round(statistics.mean(completed), 2) if completed else '',
                                *(pending[approach] for approach in ORIGINS), safety, teleports, discarded])
                for approach, edges in monitored.items():
                    for edge in edges:
                        for i in range(lane_ids[edge]):
                            lane = f'{edge}_{i}'
                            lanes.append([case, scale, approach, edge, i, round(counts[lane] / 90, 3), maxima[lane]])
    write_csv(ROOT / 'results/phase3_ablation.csv',
              ['case', 'demand_fraction', 'loaded', 'inserted', 'arrived', 'running', 'waiting',
               'mean_route_halted', 'max_route_halted', 'mean_completed_travel_s',
               'pending_link1', 'pending_link3', 'pending_link5', 'pending_link6', 'collisions', 'teleports', 'discarded'], results)
    write_csv(ROOT / 'results/phase3_lane_queues.csv',
              ['case', 'demand_fraction', 'approach', 'edge', 'lane', 'mean_halted', 'max_halted'], lanes)
    print('Wrote ablation metrics and per-lane queue snapshots')


if __name__ == '__main__':
    main()
