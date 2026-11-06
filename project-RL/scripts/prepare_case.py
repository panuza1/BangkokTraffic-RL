"""Aggregate documented loop sensors without filling missing observations."""
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SENSORS = {'Link1': range(10, 15), 'Link3': range(30, 34),
           'Link5': range(50, 54), 'Link6': range(60, 64)}
DATE = '2016-06-02'


def load_sensor(path, date=DATE):
    rows = {}
    with path.open(newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ['Date', 'Time', 'Volume', 'Occupancy']:
            raise ValueError(f'{path}: unexpected schema')
        for row in reader:
            timestamp = datetime.strptime(row['Time'], '%H:%M:%S')
            if row['Date'] != date or timestamp.second % 5 or row['Time'] in rows:
                raise ValueError(f'{path}: invalid date or duplicate/off-grid timestamp')
            values = []
            for key in ('Volume', 'Occupancy'):
                value = float(row[key]) if row[key].strip() else None
                if value is not None and (not math.isfinite(value) or value < 0 or (key == 'Occupancy' and value > 100)):
                    raise ValueError(f'{path}: invalid {key}')
                values.append(value)
            rows[row['Time']] = values
    if len(rows) != 17280:
        raise ValueError(f'{path}: expected a complete 5-second time grid, got {len(rows)}')
    return rows


def aggregate(samples):
    volumes = [v for v, _ in samples]
    occupancies = [o for _, o in samples]
    mv, mo = volumes.count(None), occupancies.count(None)
    return (sum(volumes) if not mv else '',
            round(sum(occupancies) / len(occupancies), 6) if not mo else '', mv, mo)


def main():
    base = Path('data/raw/figshare/sample/loopcoil')
    output = Path('data/processed')
    output.mkdir(parents=True, exist_ok=True)
    paths = [base / link / f"20160602_{sensor}.csv" for link, sensors in SENSORS.items() for sensor in sensors]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    all_rows = []
    for link, sensors in SENSORS.items():
        files = [load_sensor(base / link / f'20160602_{sensor}.csv') for sensor in sensors]
        for interval in range(96):
            start = datetime.strptime(DATE, '%Y-%m-%d').replace(tzinfo=ZoneInfo('Asia/Bangkok')) + timedelta(minutes=15 * interval)
            samples = [file[(start + timedelta(seconds=5 * i)).strftime('%H:%M:%S')]
                       for file in files for i in range(180)]
            count, occupancy, missing_count, missing_occupancy = aggregate(samples)
            all_rows.append([link, start.isoformat(), count, occupancy, missing_count, missing_occupancy])
    with (output / 'approach_15min_2016-06-02.csv').open('w', newline='') as dest:
        writer = csv.writer(dest)
        writer.writerow(['approach', 'local_start_assumed_bangkok', 'observed_count', 'mean_occupancy_pct',
                         'missing_volume_samples', 'missing_occupancy_samples'])
        writer.writerows(all_rows)
    manifest = {'source_doi': '10.6084/m9.figshare.14643411.v1', 'source_type': 'measured loop counts',
                'date': DATE, 'timezone': 'Asia/Bangkok (assumed; source has no offset)',
                'interval_minutes': 15, 'sensors_by_approach': {k: list(v) for k, v in SENSORS.items()},
                'missing_policy': 'leave aggregate blank if any constituent value is missing',
                'split': 'one-day exploratory case; no held-out day', 'input_sha256': hashes}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Wrote {len(all_rows)} approach intervals; incomplete count intervals: '
          f'{sum(bool(row[4]) for row in all_rows)}')


if __name__ == '__main__':
    main()
