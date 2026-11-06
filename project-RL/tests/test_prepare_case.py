import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_case import aggregate, load_sensor


class PrepareCaseTest(unittest.TestCase):
    def test_aggregate_preserves_missing(self):
        self.assertEqual(aggregate([(2.0, 10.0), (3.0, 20.0)]), (5.0, 15.0, 0, 0))
        self.assertEqual(aggregate([(2.0, None), (None, 20.0)]), ('', '', 1, 1))

    def test_reject_duplicate_and_wrong_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sensor.csv'
            path.write_text('Date,Time,Volume,Occupancy\n2016-06-02,00:00:00,1,5\n2016-06-02,00:00:00,1,5\n')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                load_sensor(path)
            path.write_text('Date,Time,Volume,Occupancy\n2016-06-02,00:00:00,1,101\n')
            with self.assertRaisesRegex(ValueError, 'invalid Occupancy'):
                load_sensor(path)
            path.write_text('Date,Time,Volume\n2016-06-02,00:00:00,1\n')
            with self.assertRaisesRegex(ValueError, 'schema'):
                load_sensor(path)

class Phase2Test(unittest.TestCase):
    def test_gap_runs_keep_sensor_multiplicity(self):
        from analyze_phase2 import gap_runs
        self.assertEqual(gap_runs([0, 2, 3, 0, 1]), [(1, 2, 5), (4, 4, 1)])
        self.assertEqual(gap_runs([0, 0]), [])

    def test_count_unit_and_missing_observation(self):
        # 180 samples are 15 minutes at five seconds; counts are not hourly rates.
        count, occupancy, missing, _ = aggregate([(1.0, 10.0)] * 180)
        self.assertEqual((count, occupancy, missing), (180, 10, 0))
        self.assertEqual(aggregate([(1.0, 10.0)] * 179 + [(None, 10.0)])[0], '')

    def test_chronological_split(self):
        from analyze_phase2 import SPLIT
        self.assertEqual(sorted(SPLIT.values()), ['test', 'training', 'validation'])
        self.assertLess(next(d for d, s in SPLIT.items() if s == 'training'),
                        next(d for d, s in SPLIT.items() if s == 'validation'))
        self.assertLess(next(d for d, s in SPLIT.items() if s == 'validation'),
                        next(d for d, s in SPLIT.items() if s == 'test'))

    def test_load_full_grid_and_reject_off_grid(self):
        from datetime import datetime, timedelta
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sensor.csv'
            start = datetime(2016, 6, 2)
            rows = ['Date,Time,Volume,Occupancy']
            rows += [f"2016-06-02,{(start + timedelta(seconds=5*i)):%H:%M:%S},1,5" for i in range(17280)]
            path.write_text('\n'.join(rows) + '\n')
            self.assertEqual(len(load_sensor(path)), 17280)
            rows[1] = '2016-06-02,00:00:01,1,5'
            path.write_text('\n'.join(rows) + '\n')
            with self.assertRaisesRegex(ValueError, 'off-grid'):
                load_sensor(path)

    def test_generated_completeness_and_strict_count(self):
        import csv
        import hashlib
        import json
        from datetime import datetime, timedelta
        from unittest.mock import patch
        import analyze_phase2
        start = datetime(2016, 6, 2)
        data = {(start + timedelta(seconds=5*i)).strftime('%H:%M:%S'): [1.0, 5.0] for i in range(17280)}
        missing_data = dict(data)
        missing_data['00:00:05'] = [None, 5.0]
        with tempfile.TemporaryDirectory() as directory:
            base, output = Path(directory) / 'raw', Path(directory) / 'out'
            for link, sensors in analyze_phase2.SENSORS.items():
                (base / 'loopcoil' / link).mkdir(parents=True)
                for sensor in sensors:
                    (base / 'loopcoil' / link / f'20160602_{sensor}.csv').touch()
            def load(path, day):
                return missing_data if path.name == '20160602_10.csv' else data
            with patch.object(analyze_phase2, 'BASE', base), patch.object(analyze_phase2, 'OUTPUT', output), \
                 patch.object(analyze_phase2, 'DAYS', ('2016-06-02',)), patch.object(analyze_phase2, 'load_sensor', side_effect=load):
                analyze_phase2.main()
            with (output / 'candidate_profiles_15min.csv').open(newline='') as f:
                rows = list(csv.DictReader(f))
            manifest = json.loads((output / 'phase2_manifest.json').read_text())
            self.assertEqual(manifest['candidate_profiles_sha256'], hashlib.sha256((output / 'candidate_profiles_15min.csv').read_bytes()).hexdigest())
            self.assertEqual(manifest['sensors_by_approach']['Link1'], [10, 11, 12, 13, 14])
            incomplete, complete = rows[0], rows[1]
            self.assertEqual(incomplete['count_completeness_pct'], '99.888889')
            self.assertEqual((incomplete['observed_vehicles_per_15min'], incomplete['status']), ('', 'missing'))
            self.assertEqual((incomplete['imputed_count'], incomplete['estimated_arrivals']), ('', ''))
            self.assertEqual((complete['count_completeness_pct'], complete['observed_vehicles_per_15min']), ('100.0', '900.0'))


if __name__ == '__main__':
    unittest.main()
