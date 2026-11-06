import copy
import csv
import subprocess
import tempfile
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_phase3 import check_network


class Phase3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.net = ET.parse('sumo/sathorn.net.xml').getroot()

    def test_network_left_hand_and_signal_safety(self):
        check_network(self.net)
        bad = copy.deepcopy(self.net)
        bad.set('lefthand', 'false')
        with self.assertRaisesRegex(ValueError, 'left-hand'):
            check_network(bad)
        bad = copy.deepcopy(self.net)
        bad.find('tlLogic').findall('phase')[1].set('duration', '1')
        with self.assertRaisesRegex(ValueError, 'yellow'):
            check_network(bad)
        bad = copy.deepcopy(self.net)
        bad.find('tlLogic').findall('phase')[2].set('state', 'G' + 'r' * 29)
        with self.assertRaisesRegex(ValueError, 'all-red'):
            check_network(bad)

    def test_conflicting_green_is_rejected(self):
        bad = copy.deepcopy(self.net)
        logic = bad.find('tlLogic')
        links = [c for c in bad.findall('connection') if c.get('tl') == logic.get('id')]
        for junction in bad.findall('junction'):
            lanes = junction.get('intLanes', '').split()
            mapped = {lanes.index(c.get('via')): int(c.get('linkIndex')) for c in links if c.get('via') in lanes}
            if not mapped:
                continue
            for request in junction.findall('request'):
                i = int(request.get('index'))
                for j in mapped:
                    if request.get('foes')[-1-j] == '1':
                        phases = logic.findall('phase')
                        g = ['r'] * len(phases[0].get('state'))
                        g[mapped[i]] = g[mapped[j]] = 'G'
                        phases[0].set('state', ''.join(g))
                        phases[1].set('state', ''.join('y' if x == 'G' else 'r' for x in g))
                        with self.assertRaisesRegex(ValueError, 'conflicting green'):
                            check_network(bad)
                        return
        self.fail('no conflict in network to test')

    def test_route_connectivity_directions_and_lanes(self):
        roads = ET.parse('sumo/sathorn.osm.xml').getroot()
        ways = {w.get('id'): {t.get('k'): t.get('v') for t in w.findall('tag')} for w in roads.findall('way')}
        for osm_id, name, lanes in [('747478914', 'Sathon Tai Road', '4'), ('295789573', 'Charoen Rat Road', '3'),
                                    ('39943703', 'Surasak Road', '4'), ('177961597', 'Sathon Nuea Road', '4')]:
            self.assertEqual((ways[osm_id].get('name:en'), ways[osm_id].get('oneway'), ways[osm_id].get('lanes')),
                             (name, 'yes', lanes))
        edges = {e.get('id'): e for e in self.net.findall('edge')}
        connections = {(c.get('from'), c.get('to')) for c in self.net.findall('connection')}
        for route in ET.parse('sumo/case.rou.xml').getroot().findall('route'):
            path = route.get('edges').split()
            self.assertTrue(all(e in edges for e in path))
            self.assertTrue(all(pair in connections for pair in zip(path, path[1:])))
        for detector in ET.parse('sumo/detectors.add.xml').getroot():
            edge, lane = detector.get('lane').rsplit('_', 1)
            self.assertLess(int(lane), len(edges[edge].findall('lane')))

    def test_simulation_is_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            additional = ET.parse('sumo/detectors.add.xml')
            for detector in additional.getroot():
                detector.set('file', str(directory / 'detectors.xml'))
            additional.write(directory / 'detectors.add.xml')
            snapshots = []
            for _ in range(2):
                subprocess.run(['.venv/bin/sumo', '-c', 'sumo/case.sumocfg',
                                '--additional-files', str(directory / 'detectors.add.xml'),
                                '--tripinfo-output', str(directory / 'trips.xml'),
                                '--statistic-output', str(directory / 'stats.xml')], check=True, capture_output=True)
                detectors = ET.tostring(ET.parse(directory / 'detectors.xml').getroot())
                trips = ET.tostring(ET.parse(directory / 'trips.xml').getroot())
                stats = ET.parse(directory / 'stats.xml').getroot()
                self.assertEqual(stats.find('safety').get('collisions'), '0')
                snapshots.append((detectors, trips, b''.join(ET.tostring(x) for x in stats if x.tag != 'performance')))
            self.assertEqual(*snapshots)

    def test_demand_is_estimated_from_complete_june2_profile(self):
        with open('data/processed/approach_15min_2016-06-02.csv', newline='') as f:
            source = {r['approach']: float(r['observed_count']) for r in csv.DictReader(f)
                      if r['local_start_assumed_bangkok'] == '2016-06-02T07:00:00+07:00' and r['missing_volume_samples'] == '0'}
        with open('sumo/demand_assumptions.csv', newline='') as f:
            estimates = list(csv.DictReader(f))
        self.assertEqual(len(estimates), 4)
        for row in estimates:
            self.assertEqual(float(row['observed_detector_count_15min']), source[row['approach']])
            self.assertAlmostEqual(float(row['estimated_boundary_arrivals_veh_per_hour']), source[row['approach']] * 0.8 * 4)
            self.assertEqual(float(row['assumed_factor']), 0.8)


if __name__ == '__main__':
    unittest.main()
