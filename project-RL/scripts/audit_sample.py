import csv, collections, datetime, glob, math, os
for kind in ('loopcoil','thermal-cctv'):
 paths = sorted(glob.glob('data/raw/figshare/sample/'+kind+'/Link*/20160602_*.csv'))
 assert len(paths) == 17, f'{kind}: expected 17 sample files, got {len(paths)}'
 for path in paths:
  with open(path, newline='', encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
  assert set(('Date','Time','Volume','Occupancy')).issubset(rows[0]), path
  times=collections.Counter(r['Time'] for r in rows if r['Time'].strip())
  missing={k:sum(not r[k].strip() for r in rows) for k in ('Date','Time','Volume','Occupancy')}
  invalid=0; zeros=0
  for r in rows:
   try:
    v,o=float(r['Volume']),float(r['Occupancy'])
    if not math.isfinite(v) or not math.isfinite(o) or v<0 or not 0<=o<=100: invalid+=1
    if v==0 and o==0: zeros+=1
   except ValueError:
    if r['Volume'].strip() and r['Occupancy'].strip(): invalid += 1
  expected={str(datetime.timedelta(seconds=i*5)).zfill(8) for i in range(17280)}
  print(kind, path.split('/')[-2]+'/'+os.path.basename(path), 'rows',len(rows),'missing',missing,'duplicates',sum(c-1 for c in times.values()),'absent_5s_slots',len(expected-set(times)),'invalid',invalid,'both_zero',zeros)
