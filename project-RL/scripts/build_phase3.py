"""Build a single illustrative, not calibrated, June 2 SUMO scenario."""
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import sumo
sys.path.insert(0, str(Path(sumo.__file__).parent / 'tools'))
import sumolib

NET = Path('sumo/sathorn.net.xml')
PROFILE = Path('data/processed/approach_15min_2016-06-02.csv')
# Each route is a synthetic one-turn allocation; IDs refer to the pinned OSM import.
ROUTES = {'Link1': ('747478914#3', '751479821#0', '747478914#4', -30),
          'Link3': ('295789573#0', '751479821#0', '295789573#0', -27),
          'Link5': ('1024938013#0', '177961597#0', '1024938013#1', -30),
          'Link6': ('39943703#7', '177961597#0', '39943703#8', -30)}


def main():
    net = sumolib.net.readNet(str(NET))
    with PROFILE.open(newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['local_start_assumed_bangkok'] == '2016-06-02T07:00:00+07:00']
    if len(rows) != 4 or {r['approach'] for r in rows} != ROUTES.keys() or any(r['missing_volume_samples'] != '0' or not r['observed_count'] for r in rows):
        raise ValueError('Need complete June 2 07:00 observations for all four approaches')
    measured = {r['approach']: float(r['observed_count']) for r in rows}
    routes = ET.Element('routes')
    detectors = ET.Element('additional')
    with Path('sumo/demand_assumptions.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['approach', 'observed_detector_count_15min', 'estimated_boundary_arrivals_veh_per_hour', 'assumed_factor', 'route'])
        for approach, (origin, destination, detector_edge, pos) in ROUTES.items():
            path, _ = net.getShortestPath(net.getEdge(origin), net.getEdge(destination), vClass='passenger')
            if not path:
                raise ValueError(f'No passenger route for {approach}')
            edges = ' '.join(e.getID() for e in path)
            # shortcut: 0.8 is illustrative, estimate a boundary flow from upstream evidence before calibration.
            rate = measured[approach] * 0.8 * 4
            ET.SubElement(routes, 'route', id=approach, edges=edges)
            ET.SubElement(routes, 'flow', id=approach, route=approach, begin='0', end='900',
                          vehsPerHour=str(rate), departLane='best', departSpeed='max')
            edge = net.getEdge(detector_edge)
            if edge.getLength() < abs(pos):
                raise ValueError(f'{detector_edge} is too short for approximate detector')
            for lane in edge.getLanes():
                ET.SubElement(detectors, 'inductionLoop', id=f'{approach}_{lane.getIndex()}',
                              lane=lane.getID(), pos=str(pos), period='900', file='../results/phase3_detectors.xml')
            w.writerow([approach, measured[approach], rate, 0.8, edges])
    ET.ElementTree(routes).write('sumo/case.rou.xml', encoding='utf-8', xml_declaration=True)
    ET.ElementTree(detectors).write('sumo/detectors.add.xml', encoding='utf-8', xml_declaration=True)
    print('Generated synthetic demand from June 2 07:00–07:15 only; no test day read.')


if __name__ == '__main__':
    main()
