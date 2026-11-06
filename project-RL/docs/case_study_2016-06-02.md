# Initial case study: 2 June 2016

This is an exploratory input audit, not a calibration or evaluation. [The dataset audit](dataset_audit.md) explains provenance, road grouping and original file checks. `python3 scripts/prepare_case.py` regenerates ignored `data/processed/approach_15min_2016-06-02.csv` and its manifest from the 17 extracted loop files.

Each row is one approach and one 15-minute interval. The observed count is the sum of five-second loop values for the sensor IDs grouped by the source authors, only when all constituent volume values are present. This sum assumes each grouped sensor corresponds to a distinct detector stream; physical lane assignment, duplicate coverage and whether stop-line counts are suitable as arrivals remain unverified. Occupancy is the arithmetic mean over sensor-time samples, only if all are present; it is not an approach-wide vehicle count. Partial intervals have blank aggregates and explicit missing-sample counts; no missing observation is replaced with zero or extrapolated. The manifest records sensor groups, input SHA-256 checksums and the policy.

The source timestamps have no offset. The generated timestamps use `+07:00` on the explicit, unverified assumption that the source uses Asia/Bangkok local time. The source records counts per five seconds, not vehicles per hour. Each complete 15-minute total is a vehicle count in that interval, not PCU/h; do not multiply it without stating the rate conversion and assumptions.

| Approach | Sensor IDs | Complete 15-minute count intervals | Incomplete intervals | Complete intervals 06:00–09:30 |
|---|---|---:|---:|---:|
| Link 1 / South Sathorn | 10–14 | 63 / 96 | 33 | 7 / 14 |
| Link 3 / Charoen Rat | 30–33 | 63 / 96 | 33 | 7 / 14 |
| Link 5 / North Sathorn | 50–53 | 63 / 96 | 33 | 7 / 14 |
| Link 6 / Surasak | 60–63 | 63 / 96 | 33 | 7 / 14 |

Missing intervals are spread across the day, so the maximum of complete intervals cannot be claimed as the day's peak. No weekday/weekend comparison or independent held-out day exists in this case. The same-day thermal dataset may help investigate missing observations, but it is a different sensor system and must not be silently substituted for loop counts.

Turning proportions, arrival processes, vehicle mix, network geometry, legal phase transitions and clearance durations have not been measured or generated here. They are future estimated/synthetic inputs, not observations. A usable demand scenario needs a justified missing-data strategy, independent checks of detector coverage and explicit turning/arrival assumptions with sensitivity analysis. No scenario or calibration result has been produced. Before final experiments, establish a separate held-out day and freeze the split; a withheld period within this day does not establish day-level generalization.

## Multi-day follow-up

The additional [Phase 2 quality report](phase2_data_quality.md) provides the full gap-run method and a proposed chronological Jun 2/3/9 split. The June 2 per-approach missing values are 33 isolated five-second timestamps, shared across all grouped sensors. Candidate complete windows common to those three days are 07:00–07:15 and 09:00–09:30; these are short and disconnected, and their signal boundary states remain unverified. The proposal requires review before any use as a final split. No imputation or estimated arrivals were produced.
