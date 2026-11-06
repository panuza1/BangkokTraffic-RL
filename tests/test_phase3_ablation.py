import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from phase3_ablation import NETWORK, ROUTES, prepare


class AblationTests(unittest.TestCase):
    def test_interventions_are_isolated_and_preserve_clearances(self):
        source = ET.parse(NETWORK).getroot()
        source_routes = ET.parse(ROUTES).getroot()
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for case in ('baseline', 'link3_free_lane', 'link6_storage', 'longer_greens'):
                prepare(case, 1, tmp)
                net = ET.parse(tmp / 'network.xml').getroot()
                routes = ET.parse(tmp / 'routes.xml').getroot()
                for before, after in zip(source.find('tlLogic').findall('phase'), net.find('tlLogic').findall('phase')):
                    self.assertEqual(before.get('state'), after.get('state'))
                    if 'G' not in before.get('state') or case != 'longer_greens':
                        self.assertEqual(before.get('duration'), after.get('duration'))
                    else:
                        self.assertEqual(after.get('duration'), '18')
                for before in source.findall('edge'):
                    after = net.find(f"edge[@id='{before.get('id')}']")
                    for a, b in zip(before.findall('lane'), after.findall('lane')):
                        delta = float(b.get('length')) - float(a.get('length'))
                        self.assertAlmostEqual(delta, 100 if case == 'link6_storage' and before.get('id') == '39943703#7' else 0)
                for a in source_routes.findall('flow'):
                    b = routes.find(f"flow[@id='{a.get('id')}']")
                    self.assertEqual(b.get('departLane'), 'free' if case == 'link3_free_lane' and a.get('id') == 'Link3' else a.get('departLane'))
                    self.assertEqual(float(b.get('vehsPerHour')), float(a.get('vehsPerHour')))
                self.assertEqual([r.attrib for r in routes.findall('route')], [r.attrib for r in source_routes.findall('route')])


if __name__ == '__main__':
    unittest.main()
