"""Report missing loop samples and candidate observed profiles, never impute."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from prepare_case import SENSORS, load_sensor, aggregate

DAYS = ('2016-06-02', '2016-06-03', '2016-06-06', '2016-06-07', '2016-06-08', '2016-06-09')
SPLIT = {'2016-06-02': 'training', '2016-06-03': 'validation', '2016-06-09': 'test'}
BASE = Path('data/raw/figshare/sample')
OUTPUT = Path('data/processed')


def gap_runs(missing):
    """Return inclusive start/end slot indices and missing-sensor samples per gap."""
    runs = []
    start = None
    total = 0
    for index, count in enumerate([*missing, 0]):
        if count and start is None:
            start = index
        if count:
            total += count
        elif start is not None:
            runs.append((start, index - 1, total))
            start, total = None, 0
    return runs


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    profiles, gaps, summaries, hashes = [], [], [], {}
    for day in DAYS:
        compact = day.replace('-', '')
        midnight = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=ZoneInfo('Asia/Bangkok'))
        signal = BASE / 'signal' / f'{day}.csv'
        if signal.exists():
            hashes[str(signal)] = hashlib.sha256(signal.read_bytes()).hexdigest()
            with signal.open(newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != ['Time', 'Mode', 'Phase', 'Duration']:
                    raise ValueError(f'{signal}: unexpected schema')
                events = list(reader)
            times = [datetime.strptime(r['Time'], '%H:%M:%S') for r in events]
            if times != sorted(set(times)):
                raise ValueError(f'{signal}: duplicate or unordered timestamps')
            in_morning = [r for r in events if '06:00:00' <= r['Time'] < '09:30:00']
            signal_summary = {'records': len(events), 'morning_records': len(in_morning),
                              'morning_lost_connection': sum('lost' in r['Mode'].lower() for r in in_morning),
                              'morning_missing_phase': sum(not r['Phase'].strip() for r in in_morning)}
        else:
            signal_summary = None
        for approach, sensors in SENSORS.items():
            paths = [BASE / 'loopcoil' / approach / f'{compact}_{sensor}.csv' for sensor in sensors]
            for path in paths:
                hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            streams = [load_sensor(path, day) for path in paths]
            missing = []
            values = []
            for i in range(17280):
                stamp = (midnight + timedelta(seconds=5*i)).strftime('%H:%M:%S')
                sample = [stream[stamp] for stream in streams]
                values.append(sample)
                missing.append(sum(v is None for v, _ in sample))
            runs = gap_runs(missing)
            for start, end, count in runs:
                gaps.append([day, approach, (midnight + timedelta(seconds=5*start)).isoformat(),
                             (midnight + timedelta(seconds=5*(end+1))).isoformat(),
                             end-start+1, (end-start+1)*5, count])
            lengths = Counter(end-start+1 for start, end, _ in runs)
            summaries.append({'date': day, 'approach': approach, 'sensor_count': len(streams),
                              'missing_sensor_samples': sum(missing), 'missing_timestamps': sum(x > 0 for x in missing),
                              'gap_lengths_5s_slots': dict(sorted(lengths.items())), 'signal': signal_summary})
            for interval in range(96):
                samples = [sample for slot in values[interval*180:(interval+1)*180] for sample in slot]
                count, _, mv, _ = aggregate(samples)
                profiles.append([day, SPLIT.get(day, 'unassigned'), approach,
                                 (midnight + timedelta(minutes=15*interval)).isoformat(),
                                 count, mv, round(100 * (len(samples) - mv) / len(samples), 6),
                                 'observed_complete' if count != '' else 'missing', '', ''])
    def write_csv(name, header, rows):
        with (OUTPUT / name).open('w', newline='') as f:
            writer = csv.writer(f); writer.writerow(header); writer.writerows(rows)
    write_csv('count_gaps.csv', ['date', 'approach', 'start_inclusive', 'end_exclusive', 'slots_5s',
                                'duration_seconds', 'missing_sensor_samples'], gaps)
    write_csv('candidate_profiles_15min.csv', ['date', 'proposed_split', 'approach', 'start_assumed_bangkok',
                                               'observed_vehicles_per_15min', 'missing_sensor_samples', 'count_completeness_pct', 'status',
                                               'imputed_count', 'estimated_arrivals'], profiles)
    manifest = {'source_doi': '10.6084/m9.figshare.14643411.v1', 'signal_and_loop_sha256': hashes,
                'candidate_profiles_sha256': hashlib.sha256((OUTPUT / 'candidate_profiles_15min.csv').read_bytes()).hexdigest(),
                'sensors_by_approach': {k: list(v) for k, v in SENSORS.items()},
                'timezone': 'Asia/Bangkok assumed, not verified', 'split': SPLIT,
                'split_status': 'proposed for review; no day-level generalization',
                'missing_policy': 'no imputation; withhold any incomplete 15-minute aggregate',
                'profile_unit': 'observed vehicles per 15-minute interval, not PCU or arrivals',
                'count_completeness_pct': '100 * present volume sensor-samples / (180 * sensors in approach), rounded to 6 decimals',
                'estimated_and_imputed_values': 'none', 'quality': summaries}
    (OUTPUT / 'phase2_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{len(profiles)} intervals; {len(gaps)} approach gap runs; '
          f'{sum(r[7] == "missing" for r in profiles)} incomplete intervals')


if __name__ == '__main__':
    main()
