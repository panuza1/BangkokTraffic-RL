# Phase 1 data feasibility audit — 2026-11-05

**Status: PASS for revised Phase 1 minimum, limited to the 2 June 2016 exploratory case.** Licensed files, schemas, timestamps, approach-level grouping, same-day signal records and missingness are evidenced below. Exact lane mapping and historical clearances are not required under the revised scope; they remain unknown. Safety, realistic topology and sensitivity to explicit clearance assumptions remain Phase 3 gates. The source timezone is unverified: interpreting it as Asia/Bangkok is an assumption. This does not establish a fully calibrated simulation, independent held-out days or generalization.

## Sources, access and licensing

| Source | Evidence and restrictions | Use decision |
|---|---|---|
| [Figshare v1 metadata](https://api.figshare.com/v2/articles/14643411/versions/1), [dataset DOI](https://doi.org/10.6084/m9.figshare.14643411.v1), [data descriptor](https://www.nature.com/articles/s41597-022-01448-6) | CC BY 4.0. Public downloadable files: signal 1,631,830 bytes, manual signal 27,420, loop coil 86,972,201, thermal 15,776,258; CCTV 260,602,498 (not downloaded). Four downloaded files matched the Figshare MD5s; see [data instructions](../data/README.md). | Candidate primary observations. Copyright attribution required. |
| [BMA intersection volumes](https://traffic.bangkok.go.th/re_intersection/intersection/intersection.html) | Monthly XLSX/PDF reports since 2016; the examined listing did not establish an explicit reuse license or file sizes. | Auxiliary only; no file downloaded or reuse assumed until terms and intersection coverage are confirmed. |
| [OTP CCTV analytics](https://data.go.th/dataset/otp_66_05), [catalog API](https://data.go.th/api/3/action/package_show?id=otp_66_05) | Public; 5–11 Sep 2022; catalog says “Open Data Common” without specifying a license variant and API `isopen` is false. XLSX 1,297,364 bytes; CSV 2,598,436 bytes. Counts are PCU/hour, density PCU/km, speed km/h; exact geographic overlap unverified. | Not joined to 2016 sensor observations; license variant and camera locations need confirmation before use. |
| [Chula-SSS GitHub](https://github.com/SathornModel/Chula-SSS), [paper](https://easychair.org/publications/paper/jDp8) | GitHub API tree contains morning/evening network and route files; the paper describes them as publicly downloadable. Root has no license and `Chula-SSS/LICENSE.txt` is zero bytes; API reports license `null`. Scenario readme calls it ongoing calibration work. | Availability confirmed; reuse rights and SUMO 1.28 compatibility **not established**. Do not copy or incorporate it until terms are clarified. |

## Observed file schemas and alignment

The descriptor reports loop data 27 May–13 Sep 2016, signal data 9 Nov 2014–14 Sep 2016, thermal 30 May–24 Jun 2016, and conventional CCTV 13 Sep 2016–23 Sep 2019. These are reported coverage bounds, not proof that every file or every hour is complete. Loop and signal can overlap over many days; thermal has a shorter overlap. Conventional CCTV overlap with loop may be only 13 Sep 2016, if the actual files support it. 2022 OTP and 2014 manual data are not same-day 2016 observations.

On **2 June 2016**, inspected actual files contain 17 loop and 17 thermal lane records and a signal record. Example loop file `loopcoil/Link1/20160602_10.csv`: `Date,Time,Volume,Occupancy`, first row `2016-06-02,00:00:00,1.0,16.0`; thermal uses the same columns but date `20160602`. Each sample file has 17,280 five-second rows. Descriptor identifies volume as vehicle counts and occupancy as a percentage; timestamps have no timezone offset. Treat Bangkok local time as a hypothesis pending confirmation. At 06:00–09:30 each sensor file has 7 missing volume and occupancy entries; signal events exist from 06:01:14 to 09:29:21 in that interval (148 rows). This establishes a candidate overlap, **not** uninterrupted valid measurements or a validated training/test split.

Signal file `signal/2016-06-02.csv` columns `Time,Mode,Phase,Duration`; first record `04:02:04, Lost Connection,,`, next `05:26:02,2,3.0,30.0`. It has 695 records, phase 1/3/4/5/6 plus one missing phase and duration, no duplicate timestamps and one zero-duration record. Recorded event times in 06:00–09:30 have a maximum consecutive gap of 207 seconds; a long phase is possible and a gap alone does not prove downtime. There is no separate yellow/all-red or pedestrian field in this schema. Meaning of `Mode`, clearance representation, exact legal transitions and min/max green are not established from these rows. The paper describes eight phases and common sequences 1–3–5 and 1–3–1–5, but phase drawings and historical records alone do not establish safe transition timing.

The authors' [notebook](https://github.com/EEM0N/sathorndata.github.io/blob/main/sathorndata.ipynb) groups loop/thermal IDs as Link 1: 10–14; Link 3: 30–33; Link 5: 50–53; Link 6: 60–63. The paper identifies Link 1 as South Sathorn, Link 3 Charoen Rat, Link 5 North Sathorn, and Link 6 Surasak; these are the four approaches. Exact sensor-to-lane/turning movement and the correspondence of those lanes to a network still require validation against its sensor map (Fig. 3), road geometry, and phase movements (Fig. 4). Do not treat ID grouping as a validated lane connection.

## Sample quality: 2 June 2016

All 34 files have 17,280 distinct five-second timestamps, zero absent five-second slots, no negative volume or occupancy outside 0–100 in nonempty numeric values. Counts below are per file and apply to both volume and occupancy; empty timestamp rows are not the same as a verified sensor outage. Full per-sensor counts and both-zero observations are in [sample quality](sample_quality_2016-06-02.txt); the script flags simple ranges only, not every anomaly.

| Sensor group | Files | Missing cells per measured column per file | Duplicate timestamps | Absent 5-second slots | Out-of-range numeric values |
|---|---:|---:|---:|---:|---:|
| Loop, all links | 17 | 33 (0.19%) | 0 | 0 | 0 |
| Thermal, links 1 and 3 | 9 | 862 (4.99%) | 0 | 0 | 0 |
| Thermal, links 5 and 6 | 8 | 47 (0.27%) | 0 | 0 | 0 |

Both volume and occupancy can be zero during normal operation; zero runs were not classified as sensor downtime. Missing-value runs and all remaining candidate days must be examined before day selection. This is a one-day feasibility sample, not a dataset-wide quality report.

## Other validation targets and outstanding decisions

- Queue and turning flows: manual archive and paper describe 31 July 2014 measurements; whether files supply movement-resolved flows and units suitable as assumptions remains to be verified. They cannot be silently joined to 2016. Queue observations for the 2016 calibration day are not established.
- GPS: Figshare lists taxi observations and a small speed CSV; the descriptor reports six days including 2 June 2016. Their exact schema, route and suitability as independent travel-time targets remain unverified.
- Road geometry: sensor/phase figures are available in the descriptor; historical lane topology and near-intersection effects have not been verified against a usable network.
- Request the source owners' documentation for signal mode, start/end semantics, yellow/all-red/pedestrian timing, exact lane mappings and timestamp timezone. Review license or obtain permission before using Chula-SSS. The user approved explicit simulation-only assumptions for unknown clearances and approach-level counts. These cannot be represented as measurements or as a validated historical phase program; safety and sensitivity testing remain mandatory.
- Start Phase 2 using the documented one-day case at approach level. Before any final research comparison, audit multiple days and preselect distinct calibration and held-out days; a single day cannot support a day-held-out claim.

## Multi-day Phase 2 follow-up — 2026-11-06

The audit now includes loop data for 2, 3, 6, 7, 8 and 9 June 2016 and signal archives for all except 7 June. Quality, signal-event limitations, chronological split proposal, gaps and missing-data policy are documented in [Phase 2 data quality](phase2_data_quality.md). The evidence supports candidate Bangkok-informed profiles only; it does not establish a calibrated simulation. Jun 2/3/9 are proposed as training/validation/test days, pending review, and are not sufficient to establish generalization.
