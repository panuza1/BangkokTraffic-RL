"""Summarize illustrative detector results without treating them as calibration."""
import collections
import csv
import xml.etree.ElementTree as ET

hits = collections.Counter()
for interval in ET.parse('results/phase3_detectors.xml').getroot().findall('interval'):
    if float(interval.get('begin')) != 0 or float(interval.get('end')) != 900:
        raise ValueError('expected one 900-second detector interval')
    hits[interval.get('id').split('_')[0]] += int(interval.get('nVehEntered'))
with open('sumo/demand_assumptions.csv', newline='') as src, open('results/phase3_comparison.csv', 'w', newline='') as dst:
    rows = list(csv.DictReader(src))
    if set(hits) != {r['approach'] for r in rows}:
        raise ValueError('detector approaches do not match demand')
    w = csv.writer(dst)
    w.writerow(['approach', 'observed_detector_count_15min', 'estimated_boundary_arrivals_veh_per_hour', 'simulated_detector_entries_15min'])
    for row in rows:
        w.writerow([row['approach'], row['observed_detector_count_15min'],
                    row['estimated_boundary_arrivals_veh_per_hour'], hits[row['approach']]])
print('Wrote results/phase3_comparison.csv')
