# Data sources and reproduction

Raw files and extracted samples are local and ignored by Git. The source [Figshare version 1](https://figshare.com/articles/dataset/Real-world_sensor_dataset_for_city_inbound-outbound_critical_intersection_analysis/14643411/1) is CC BY 4.0: credit its authors, cite DOI 10.6084/m9.figshare.14643411.v1, link the license, and indicate changes when sharing derived material. Inspect its [metadata](https://api.figshare.com/v2/articles/14643411/versions/1) before downloading. The following files total about 104.4 MB compressed; extracted files require additional space. Other sources and unresolved terms are documented in [the audit](../docs/dataset_audit.md).

```sh
mkdir -p data/raw/figshare/sample
curl -fL https://ndownloader.figshare.com/files/28369986 -o data/raw/figshare/signal.rar
curl -fL https://ndownloader.figshare.com/files/34026611 -o data/raw/figshare/manual-signal.rar
curl -fL https://ndownloader.figshare.com/files/29021775 -o data/raw/figshare/loopcoil.rar
curl -fL https://ndownloader.figshare.com/files/29021763 -o data/raw/figshare/thermal-cctv.rar
md5sum data/raw/figshare/{signal,manual-signal,loopcoil,thermal-cctv}.rar
# With a RAR-capable unrar installed:
unrar x -o+ -idq data/raw/figshare/signal.rar signal/2016-06-02.csv data/raw/figshare/sample/
unrar x -o+ -idq data/raw/figshare/loopcoil.rar '*/20160602_*.csv' data/raw/figshare/sample/
unrar x -o+ -idq data/raw/figshare/thermal-cctv.rar '*/20160602_*.csv' data/raw/figshare/sample/
python3 scripts/audit_sample.py
```

Expected MD5, in the order above: `43f6d82f6fd16a915f6b39d024776074`, `80b4d0946f50decf72e09fdf0acddbb5`, `2d73518a5ff0e56c0b8b0c67b767ee00`, `8c58b2eaf7d70aecfd7a9bb097dd0876`. The audit ran with Ubuntu's locally extracted `unrar-nonfree` 6.1.5; the installed 7-Zip could list but could not extract this RAR compression method. The manual signal sample was inspected directly using `unrar p` and is from 2014, not the 2016 sample.

## Generate the exploratory case

After extracting the June 2 sample above, run `python3 scripts/prepare_case.py`. It creates a 15-minute approach-level observation table and a manifest in ignored `data/processed/`; rerunning uses the source samples and records their SHA-256 hashes. See [the case report](../docs/case_study_2016-06-02.md) for units, completeness, and why the table is not yet SUMO demand.

## Multi-day gap audit and candidate profiles

Extract the additional dates from the already downloaded archives (Jun 7 has no signal file):

```sh
for day in 03 06 07 08 09; do
  unrar x -o+ -idq data/raw/figshare/loopcoil.rar "*/201606${day}_*.csv" data/raw/figshare/sample/
done
for day in 03 06 08 09; do
  unrar x -o+ -idq data/raw/figshare/signal.rar "signal/2016-06-${day}.csv" data/raw/figshare/sample/
done
python3 scripts/analyze_phase2.py
python3 -m unittest discover -s tests -v
```

Outputs are ignored `data/processed/count_gaps.csv`, `data/processed/candidate_profiles_15min.csv`, and `data/processed/phase2_manifest.json`; see [the quality report](../docs/phase2_data_quality.md) before using any profile. The split is a proposal and requires review, not an approved final evaluation protocol.

`count_completeness_pct` in `data/processed/candidate_profiles_15min.csv` is the percentage of present five-second volume sensor-samples out of 180 × the number of sensors in that approach, rounded to six decimal places. It is not a percentage of traffic observed. An incomplete interval retains a blank observed count, regardless of its percentage. The manifest records input hashes, sensor groups and the generated CSV's SHA-256.
