# BangkokTraffic-RL — Implementation Plan for Codex

> สถานะ: **พร้อมเริ่ม Phase 0**  
> ประเภท: Research-first / Simulation-only  
> พื้นที่เริ่มต้น: **แยกสาทร–สุรศักดิ์ (Sathorn–Surasak), กรุงเทพมหานคร**  
> เป้าหมาย: สร้างและประเมินระบบควบคุมไฟจราจรด้วย Reinforcement Learning บน SUMO โดยใช้ข้อมูลจริงของกรุงเทพฯ เป็นข้อมูลตั้งต้น และระบุขอบเขตการ calibration อย่างตรงไปตรงมา

## Revised MVP scope — 2026-11-05 (supersedes conflicting text below)

- Case study: 2 June 2016, using Figshare's measured loop counts aggregated by documented approach and same-day signal events. Treat timestamp timezone as an explicit, unverified Asia/Bangkok assumption. No sensor-to-lane assignment is inferred.
- Build an independent single-intersection OSM/SUMO network; Chula-SSS is not required and must not be incorporated without clear rights. OSM licensing and topology must be checked before use.
- Yellow/all-red and other unknown signal inputs are explicit simulation assumptions, not historical measurements; define safe conflict-free transitions and test sensitivity to their values. Pedestrian movements require evidence or explicit scope and safety handling. No real-world deployment.
- Initial case-study demand may use estimated turning ratios and synthetic routing only if individually labeled and sensitivity-tested; never fill or portray missing counts as measured. Distinguish measured, estimated/assumed, synthetic and simulated outputs in every artifact.
- G1 minimum for starting Phase 2: licensed real files, provenance, schema, timestamps, same-day measured counts mapped to approaches and documented missingness, plus phase evidence/known uncertainties. Historical clearances, lane mapping and Chula-SSS are not prerequisites.
- A single day cannot establish day-held-out validation or generalization. Phase 2 may prepare the initial case and identify candidate withheld time windows, but must not mark day-held-out validation complete. For final research comparison, obtain independent held-out days and freeze splits/configuration before testing; otherwise stop at a clearly labeled exploratory case study. No fabricated calibrated or performance claims.
- G3 safety remains mandatory: actual collision-free movements and valid transitions on the resulting network, explicit clearance assumptions and sensitivity tests, and honest validation evidence. If topology or safety cannot be established, or calibration falls short of an independently specified target, stop relevant work and report the limitation; do not describe the model as fully calibrated.

## 1. เป้าหมายและขอบเขต

**Research question:** เมื่อใช้สถานการณ์จราจรที่จำลองจากข้อมูลจริงของกรุงเทพฯ DQN สามารถลดเวลารอและความยาวแถวรถเมื่อเทียบกับ Fixed-time, Webster และ Max-pressure ได้หรือไม่?

**ต้องได้เมื่อจบ MVP**

- Dataset audit พร้อมอธิบาย provenance, schema, ช่วงเวลาที่ใช้ได้ และ missing values
- SUMO network สำหรับแยกสาทร–สุรศักดิ์ 1 แห่ง พร้อม traffic demand และ signal phases ที่ตรวจสอบแล้ว
- หลักฐานว่า simulation ใกล้เคียงข้อมูลจริงในชุด validation มากเพียงใด (รวมถึงข้อจำกัด)
- Controller 4 แบบ: Fixed-time, Webster, Max-pressure, DQN
- การทดลองที่ทำซ้ำได้บน traffic scenarios และ random seeds เดียวกัน
- ตาราง/กราฟ evaluation, ข้อค้นพบทั้งบวกและลบ, README และรายงานวิธีทดลอง

**ยังไม่ทำใน MVP**

- ควบคุมไฟจราจรจริงหรือเชื่อมต่อโครงสร้างพื้นฐานภาครัฐ
- ใช้ CCTV สด, Computer Vision, LLM หรือ dashboard แบบ real-time โดยไม่มีความจำเป็น
- จำลองกรุงเทพฯ ทั้งเมือง, Multi-Agent RL หรือ Multi-intersection ตั้งแต่ต้น
- อ้างว่า model ใช้ได้กับการจราจรกรุงเทพฯ ปัจจุบันโดยไม่มีข้อมูลใหม่ยืนยัน

## 2. คำสั่งสำหรับ Codex (อ่านก่อนเริ่ม)

1. ทำงานตาม Phase 0 → 6 ตามลำดับ **ห้ามข้าม Dataset Audit และ Calibration เพื่อไป train RL**
2. ก่อนแก้โค้ดให้ตรวจ repository, `AGENTS.md`, dependency และไฟล์ที่มีอยู่ก่อนเสมอ; เก็บการแก้ไขเดิมของผู้ใช้ไว้
3. ทำเฉพาะงานของ Phase ปัจจุบัน; ใช้วิธีที่เรียบง่ายที่สุด หลีกเลี่ยง refactor หรือ feature ที่ไม่เกี่ยวข้อง
4. ทุก Phase ต้องมี: implementation, test/verification, artifact, สรุปผล และอัปเดต `progress.md`
5. หลังจบ Phase ให้บันทึก: สิ่งที่ทำ, ไฟล์ที่เปลี่ยน, คำสั่งที่ทดสอบ, PASS/FAIL, ข้อจำกัด, Next Step
6. ถ้า **ข้อมูลเข้าไม่ถึง / license ไม่ชัด / topology ไม่ตรง / calibration ไม่ผ่าน / ผลทดสอบไม่เสถียร** ให้หยุดและแจ้งผู้ใช้พร้อมหลักฐาน ห้ามแต่งข้อมูลหรือแสดงว่า PASS
7. ไม่ดาวน์โหลดข้อมูลจำนวนมากโดยไม่ประเมินขนาดและข้อกำหนดการใช้งานก่อน; ไม่ commit raw dataset ที่มีขนาดใหญ่หรือสิทธิ์ไม่ชัด
8. ไม่ push, merge, deploy หรือใช้บริการเสียเงินโดยไม่ได้รับคำสั่งเพิ่มเติม; local commits แยก Phase ทำได้เมื่อ repository สะอาดพอและผู้ใช้อนุญาต
9. ให้ผู้ใช้ตรวจสอบผลได้ทุก Phase และทำงานต่อเมื่อเกณฑ์ผ่าน; ประเด็นที่ต้องตัดสินใจใหม่ให้รอคำตอบผู้ใช้
10. ข้อสรุปต้องแยก **measured data**, **assumptions**, **simulation outputs**, และ **inferences** ชัดเจน

## 3. แหล่งข้อมูลและงานวิจัยหลัก

| แหล่งข้อมูล | ใช้ทำอะไร | ข้อควรระวัง |
|---|---|---|
| [Sathorn real-world sensor dataset (Figshare)](https://doi.org/10.6084/m9.figshare.14643411.v1) | ปริมาณรถ, occupancy, historical signal, validation | ไฟล์/สิทธิ์/ความครบถ้วนต้องตรวจจริง |
| [Scientific Data paper (2022)](https://www.nature.com/articles/s41597-022-01448-6) | Data dictionary, sensor mapping, ช่วงเวลาที่มีข้อมูล | CCTV 2016–2019; loop และ signal มีช่วงซ้อนทับบางส่วน |
| [Sathorn preprocessing notebook](https://github.com/EEM0N/sathorndata.github.io/blob/main/sathorndata.ipynb) | อ้างอิงการ preprocess และอ่านความหมายคอลัมน์ | อย่าคัดลอก assumptions โดยไม่ตรวจ |
| [BMA intersection traffic volume](https://traffic.bangkok.go.th/re_intersection/intersection/intersection.html) | เปรียบเทียบปริมาณรถตามแยก/ช่วงเวลาที่ยาวกว่า | รายเดือนและช่วงเวลาเป็นกลุ่มใหญ่; ไม่ใช่ sensor 5 วินาที |
| [OTP CCTV traffic analytics](https://data.go.th/dataset/otp_66_05) | ปริมาณรถ/ความเร็ว/ความหนาแน่นเป็น auxiliary validation | ตรวจตำแหน่งกล้องและช่วงเวลาที่ตรงกับพื้นที่ก่อน |
| [Chula-SSS (2018)](https://easychair.org/publications/paper/jDp8) | แหล่งอ้างอิง optional | มี scenario แต่สิทธิ์ยังไม่ชัด; ไม่ใช่ dependency |
| [Sathorn SUMO study (2017)](https://doi.org/10.1109/ACCESS.2017.2739240) | อ้างอิงการ calibration และ signal optimization | ห้ามถือว่าพารามิเตอร์จาก paper ตรงกับ SUMO เวอร์ชันปัจจุบัน |
| [SUMO OSM import](https://eclipse.dev/sumo/docs/Networks/Import/OpenStreetMap.html) และ [TraCI](https://eclipse.dev/sumo/docs/TraCI/index.html) | สร้างถนนและควบคุม simulation | ตรวจ left-hand traffic, lane connections และ yellow/all-red |

**ความสำคัญของช่วงข้อมูล:** historical signal data ส่วนใหญ่อยู่ช่วง 2014–2016; loop sensor อยู่ปี 2016; CCTV traffic counts จำนวนมากอยู่ช่วง 2016–2019 จึงต้อง **เลือกช่วงเวลาที่ทับซ้อนกันจริง** สำหรับ calibration/validation และห้าม join คนละวัน/ปีราวกับเป็น observation เดียวกัน

## 4. โครงสร้าง repository เป้าหมาย (สร้างเฉพาะเมื่อจำเป็น)

```text
BangkokTraffic-RL/
├── README.md
├── PLAN.md                         # สำเนา plan นี้ใน repository
├── progress.md
├── requirements.txt                # ใช้เวอร์ชันที่ตรวจว่ารองรับกันจริง
├── data/
│   ├── README.md                   # แหล่งดาวน์โหลด + วิธี reproduce
│   ├── raw/                        # gitignored
│   └── processed/                  # generated, gitignored ถ้าขนาดใหญ่
├── configs/                        # config สำหรับ scenarios/experiments
├── sumo/                           # network, routes, signals, configuration
├── src/                            # data, simulation, controllers, training
├── scripts/                        # entry points ที่จำเป็นเท่านั้น
├── tests/
├── results/                        # metrics และ plots (ไฟล์เล็กเท่านั้น)
└── docs/
    ├── dataset_audit.md
    ├── calibration.md
    └── evaluation.md
```

หมายเหตุ: ถ้าจะทำใน repository ที่มีอยู่แล้ว ให้ปรับตามโครงสร้างเดิมโดยไม่สร้าง package ซ้ำซ้อน

---

## Phase 0 — Repository & Reproducibility Setup

**เป้าหมาย:** ทำให้คนอื่นเปิดโปรเจกต์แล้วรู้ว่าจะรันอะไร และ Codex ดำเนินงานได้โดยไม่ทับของเดิม

- [ ] ตรวจ repo/branch/working tree และคำสั่งใน `AGENTS.md` (ถ้ามี)
- [ ] สร้าง `README.md`, `progress.md`, `.gitignore` และ plan ใน repository
- [ ] บันทึก Python, SUMO, OS และ dependency versions ที่มีอยู่จริง
- [ ] ตั้งค่า seed strategy และกำหนด artifact paths
- [ ] สร้าง minimal smoke test ตรวจว่า Python และ SUMO เรียกได้ (ไม่ต้องสร้างโมเดล)

**Definition of Done:** มีคำสั่ง setup และ smoke-test ที่ทำซ้ำได้; ไม่มีการแก้ไฟล์นอกขอบเขต

**Review point:** ผู้ใช้ตรวจชื่อ repository, branch และขอบเขตงาน

## Phase 1 — Data Acquisition & Feasibility Audit [Critical Gate]

**เป้าหมาย:** ยืนยันด้วยไฟล์จริงว่าเรามีข้อมูลเพียงพอสำหรับจำลองแยกสาทร–สุรศักดิ์

- [ ] ตรวจ metadata, ขนาด, license, เงื่อนไขดาวน์โหลด ของ Figshare / BMA / OTP ก่อนดาวน์โหลด
- [ ] ดาวน์โหลดชุดเล็กที่เกี่ยวข้องก่อน แล้วตรวจไฟล์จริง: filename, schema, units, timestamp, sensor ID, location
- [ ] หา time window ที่ **loop volume + occupancy + signal history** มีช่วงทับซ้อนและคุณภาพเหมาะสม
- [ ] ตรวจ phase ID/order และบันทึกข้อมูล yellow/all-red ที่ไม่มีเป็น simulation assumption พร้อม sensitivity test
- [ ] ตรวจความพร้อมของ turning ratios, queue observations, GPS travel time และ road geometry
- [ ] ทำตาราง missing data, duplicate timestamps, abnormal values, sensor downtime
- [ ] ตรวจว่ามี Chula-SSS scenario download จริงหรือไม่ (อย่า assume ว่า paper = downloadable code)
- [ ] สร้าง `docs/dataset_audit.md` และ `data/README.md` พร้อม direct source URLs และวิธีดาวน์โหลดซ้ำ

**Definition of Done:** ตอบได้ว่า “ใช้ข้อมูลอะไร จากวันใด ที่ sensor ไหน เพื่อ calibrate อะไร” พร้อมตัวอย่าง schema จากไฟล์จริง

**Revised G1:** มีไฟล์จริงที่มีสิทธิ์ใช้งาน schema เวลา counts ที่ map ได้ระดับ approach ข้อมูล phase และข้อจำกัดที่ตรวจสอบแล้ว; ไม่บังคับ lane mapping หรือ historical clearance ที่วัดจริง แต่ต้องบันทึก assumptions และห้ามอ้างว่าเป็น observed

**Review point:** ผู้ใช้อนุมัติชุดข้อมูลหลัก, time window และ assumptions ที่จำเป็น

## Phase 2 — Data Cleaning, EDA & Traffic Demand

**เป้าหมาย:** เปลี่ยน measured data ให้เป็น input และ independent reference สำหรับ SUMO

- [ ] Load/normalize timezones เป็น `Asia/Bangkok` และรวมข้อมูลเฉพาะ source/time window ที่เทียบกันได้
- [ ] ตรวจ unit ของ counts (5-second counts, hourly counts, PCU/h) และแปลงอย่างระมัดระวัง
- [ ] Map sensor ID → documented approach; lane/turn mapping only when supported by evidence
- [ ] สรุป per-approach coverage และ profile ของวันตัวอย่าง; เปรียบเทียบ weekday/weekend เมื่อมีหลายวันที่ตรวจสอบแล้ว
- [ ] สำหรับ case วันเดียวเตรียมข้อมูล exploratory โดยไม่อ้าง day-held-out; ก่อน final evaluation ต้องมี calibration/training และ **held-out validation/test ตามวัน** (ห้ามสุ่มแถวติดกัน)
- [ ] เตรียม traffic demand และ turning-flow assumptions โดยแยก measured/estimated/synthetic; ห้ามสร้าง lane mapping เท็จ และต้องตรวจ sensitivity
- [ ] สร้าง data quality report และ plots เมื่อ coverage รองรับ; ทดสอบ schema, units และ timestamp

**Definition of Done:** ได้ `data/processed/` ที่ reproduce ได้ด้วยสคริปต์และ dataset manifest; initial case ระบุว่าไม่มี held-out days และ final evaluation ต้องมี held-out days ที่ไม่ใช้ปรับโมเดล

**Review point:** ตรวจ peak patterns และความสมเหตุสมผลของ demand/turning ratios

## Phase 3 — Build & Calibrate SUMO [Critical Gate]

**เป้าหมาย:** มี simulation ของแยกสาทร–สุรศักดิ์ที่เทียบกับ measured traffic ได้จริง

- [ ] สร้าง **network เฉพาะแยกเดียว** ด้วย OSM + SUMO พร้อมตรวจ OSM license; ไม่ต้องใช้ Chula-SSS
- [ ] ตรวจ lane count, approach, turning lanes, direction, connections, left-hand traffic, speed, stop lines และ intersections ใกล้เคียงที่มีผลต่อคิว
- [ ] นิยาม legal signal phases และ transitions ที่ปลอดภัย; ระบุ min green, yellow/all-red และ pedestrian rules ที่เป็น assumptions และทดสอบ sensitivity
- [ ] สร้าง vehicle demand สำหรับช่วงเวลาที่เลือก พร้อม random seed
- [ ] เพิ่ม detector outputs สำหรับ volume, queue, waiting time, travel time
- [ ] Calibrate โดยใช้ **calibration days เท่านั้น**: arrival rate, turning ratios, vehicle mix, driving parameters ตามข้อมูลที่รองรับ
- [ ] ประเมิน validation days แยก: counts error (MAE/RMSE), queue/occupancy/travel-time error เมื่อมี observed target
- [ ] บันทึก error by approach/time, calibration parameters, assumptions และ sensitivity analysis ใน `docs/calibration.md`
- [ ] **ตั้งเกณฑ์ยอมรับ calibration ก่อนดูผล test สุดท้าย** และบันทึกเหตุผลทาง traffic engineering

**Definition of Done:** SUMO เปิด/รันซ้ำได้, phase ถูกกฎ, demand ไม่ผิดหน่วย, และมี measured-vs-simulated validation report

**Hard Stop:** ถ้า topology/phase ไม่ปลอดภัย หรือ calibration ไม่ผ่านเกณฑ์ที่ประกาศไว้ ให้หยุดและรายงาน ห้ามอ้างว่า fully calibrated หรืออ้าง validated Bangkok improvement

**Review point:** ผู้ใช้ตรวจ SUMO GUI screenshot/video สั้น, แผนที่ lane/phase, calibration errors

## Phase 4 — Conventional Baselines

**เป้าหมาย:** มีจุดเปรียบเทียบที่แข็งแรงก่อนพัฒนา AI

- [ ] Implement **Fixed-time** (ใช้ observed timing ที่ใช้เทียบได้ หรือ documented configuration)
- [ ] Implement **Webster** signal timing โดยบันทึก assumptions และ constraint handling
- [ ] Implement **Max-pressure** หรือ actuated baseline ที่อ่าน sensor state เดียวกับ RL ได้
- [ ] บังคับทุก controller ใช้ legal phases, safety intervals และ demand scenarios เดียวกัน
- [ ] วัด average waiting time, queue length, max queue/spillback, travel time, throughput
- [ ] ทดสอบ invariants: ไม่เกิด conflicting greens, yellow/all-red ไม่ถูกข้าม, episode จบสมบูรณ์, output reproducible

**Definition of Done:** Baseline ทั้งสามรันสำเร็จและให้ metrics ที่มีหน่วย/นิยามตรงกัน

**Review point:** ผู้ใช้ตรวจ baseline table และเลือก primary metric (แนะนำ average waiting time)

## Phase 5 — Reinforcement Learning (DQN)

**เป้าหมาย:** ฝึกตัวควบคุมที่เรียนรู้การเลือก phase/ขยายเวลาไฟเขียวใน SUMO

- [ ] กำหนด `state`: normalized queue/occupancy, current phase, elapsed green (ใช้เฉพาะข้อมูลที่ agent เห็นได้จริง)
- [ ] กำหนด `action`: extend current phase หรือ advance ตาม legal transition; ไม่เปิดทุก phase โดยอิสระ
- [ ] กำหนด `reward`: negative accumulated waiting/queue cost ภายในช่วงควบคุม และกำหนดน้ำหนักคงที่ก่อน experiment
- [ ] สร้าง environment interface ตาม Gymnasium API ปัจจุบันที่ตรวจจาก installed version
- [ ] Implement DQN แบบเล็กเท่าที่จำเป็น (replay buffer, target network, epsilon-greedy)
- [ ] Train บน training scenarios เท่านั้น; ทำ evaluation แบบ deterministic policy บน held-out scenarios
- [ ] เก็บ seed, checkpoints, reward curve, hyperparameters, train time และ inference latency
- [ ] Unit tests สำหรับ observation/action shapes, reward calculation, illegal phase prevention และ reproducibility

**Definition of Done:** train/eval แยกกันชัดเจน, DQN ไม่ละเมิด phase constraints, และมี checkpoint ที่ load มาประเมินซ้ำได้

**Review point:** ผู้ใช้ตรวจ training curve, runtime, ตัวอย่างการเปลี่ยน phase และผลเทียบเบื้องต้น

## Phase 6 — Final Evaluation & Research Report

**เป้าหมาย:** สรุปอย่างตรงไปตรงมาว่า DQN ดีกว่า baseline จริงหรือไม่ใน simulation นี้

- [ ] Freeze trained models, calibration settings และ experiment configs ก่อน final test
- [ ] Run controllers ทั้ง 4 ด้วย **held-out traffic scenarios และ paired random seeds เดียวกัน**
- [ ] ทดสอบช่วงเช้า/เย็น, traffic ปกติ/มาก, ความคลาดเคลื่อนของ demand และ incident ถ้าจำลองอย่างสมเหตุสมผลได้
- [ ] รายงานค่าเฉลี่ย, ส่วนเบี่ยงเบน และ 95% confidence interval ต่อ metric
- [ ] คำนวณ relative improvement (%) เทียบแต่ละ baseline โดยกำกับว่าดี/แย่
- [ ] แสดงทั้ง primary metric และ trade-offs (เช่น ลดค่าเฉลี่ยแต่บาง approach รอนานขึ้นหรือไม่)
- [ ] Ablation เท่าที่จำเป็น: queue-only reward vs waiting-time reward; optional forecast feature ถ้ามีหลักฐานว่าช่วย
- [ ] เขียน `docs/evaluation.md`, `results/summary.csv`, ตาราง, plots และ reproducible instructions
- [ ] บอกข้อจำกัด: historical data, turning assumptions, simulation-to-real gap, unavailable sensors, no real-world deployment

**Definition of Done:** ผู้ใช้/ผู้ตรวจสามารถ rerun evaluation จาก config และ checkpoint แล้วได้ผลใกล้เดิม; สรุป **แม้ผล DQN ไม่ชนะ**

**Review point:** ตรวจทุกตารางและข้ออ้างก่อนเขียน paper/เผยแพร่

## 5. Evaluation Protocol ที่ต้องล็อกไว้

### Primary metric

`Average waiting time (seconds per vehicle)` บน completed + active vehicles ตามนิยามที่เลือกและใช้เหมือนกันทุก controller (ต้องบันทึก denominator และ horizon ชัดเจน)

### Secondary metrics

- Mean / max queue length (vehicles หรือ meters; ห้ามปะปน)
- Mean travel time (seconds/completed vehicle)
- Throughput (vehicles completed per simulated hour)
- Queue spillback events และ per-approach fairness
- Runtime: training time และ inference/decision latency

### Comparison rules

1. ใช้ network, demand, routes, episode horizon, warm-up period และ seeds เดียวกันทุก controller
2. ใช้ข้อมูล train สำหรับ tuning; test data ใช้ครั้งสุดท้ายและไม่เลือก checkpoint จาก test
3. ต้องมีอย่างน้อยหลาย independent seeds; บันทึกจำนวนจริงก่อนสรุป significance
4. Report ค่าเป็น **actual simulation result เท่านั้น**; ไม่มีการกรอก percentage improvement ก่อนรัน
5. หาก simulation/calibration ไม่ถึงเกณฑ์ ให้ระบุผลเป็น synthetic-case study ไม่ใช่ “validated Bangkok improvement”

## 6. Quality Gates / Stop Conditions

| Gate | ผ่านเมื่อ | ถ้าไม่ผ่าน |
|---|---|---|
| G1 Data | มีไฟล์จริงที่อนุญาต + schema + timestamps + approach mapping + provenance; lane mapping ไม่บังคับ | หยุดและรายงาน missing source |
| G2 Alignment | volumes/signals ใช้ช่วงที่เทียบได้ และแยก observed/estimated | จำกัดขอบเขตหรือเปลี่ยน scenario พร้อมขอผู้ใช้ตัดสินใจ |
| G3 SUMO Validity | topology/phase/units ถูกต้องและมี validation report ตามเกณฑ์ล่วงหน้า | ห้ามเริ่ม RL claim |
| G4 Baseline | 3 controllers รันได้บน identical demand | แก้ baseline ก่อน |
| G5 DQN | train/load/eval ได้, action ถูกกฎ, tests ผ่าน | แก้หรือรายงาน blockers |
| G6 Final | rerun ได้, results/plots/report ตรงกัน, ไม่มี fabricated metrics | ไม่ประกาศเสร็จ |

## 7. Progress Log Template

ให้ Codex เติมใน `progress.md` เมื่อจบแต่ละรอบ:

```markdown
## YYYY-MM-DD — Phase X: <name>
- Status: PASS / FAIL / BLOCKED
- Completed:
- Files changed:
- Commands/tests run:
- Evidence/results:
- Assumptions and limitations:
- Decisions needed from user:
- Next step:
```

## 8. Backlog หลัง MVP (ยังไม่เริ่ม)

- [ ] เพิ่มหลายแยกตามแนวสาทร พร้อม network coordination / Multi-Agent RL
- [ ] ทดสอบ generalization ข้ามวันและข้ามสี่แยก (ต้องมี ground truth ในพื้นที่ใหม่)
- [ ] Integrate live video / CV เฉพาะเมื่อมีสิทธิ์และ dataset ที่เหมาะสม
- [ ] Dashboard สาธิตกลยุทธ์ไฟจราจรและผลเปรียบเทียบ
- [ ] เขียน paper สำหรับส่งงานวิจัยเมื่อ methodology และ results ผ่านการตรวจ

---

## 9. Prompt สำหรับสั่ง Codex เริ่มงาน (Copy/Paste)

```text
Read PLAN.md in full and follow its instructions. Work on BangkokTraffic-RL
one phase at a time, starting at Phase 0. Do not skip the data feasibility
audit or SUMO calibration gates. Use a minimal, reproducible implementation.

For each phase:
1. Inspect existing repo files and instructions before editing.
2. Implement only the current phase and run relevant verification.
3. Update progress.md with evidence, tests, assumptions, blockers, and next step.
4. Summarize what I should review. Never invent data or performance results.

Stop and ask me when a quality gate fails, data or licensing is unclear,
a new major scope decision is needed, or external spending/permissions are
required. Do not push, merge, deploy, or touch real traffic infrastructure.
Start with Phase 0 now.
```

## 10. Definition of Project Complete

- [ ] G1–G6 ผ่าน หรือทุกข้อจำกัดสำคัญมีการระบุอย่างตรงไปตรงมา
- [ ] มี reproducible experiment แบบ one-command หรือ documented commands
- [ ] มี baseline vs DQN table และภาพประกอบอย่างน้อย waiting time/queue/throughput
- [ ] มีหลักฐาน calibration กับ Bangkok observed data ไม่ใช่แค่ screenshot SUMO
- [ ] README อธิบาย setup, run, sources, licensing, limitations และวิธีอ่านผล
- [ ] ผู้ใช้ตรวจและยอมรับผลก่อนนำไปอ้างใน portfolio/research paper
