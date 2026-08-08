# FEAR — Flow-based Explainable Anomaly Recognition

A hybrid unsupervised machine learning framework for flow-based, explainable anomaly detection in encrypted network traffic. 

**Core idea:** detect suspicious network activity using only flow-level metadata (packet size, timing, direction) — no payload decryption required.

---

## Progress Tracker

### Week 1 — Foundation & Data
- [x] Ubuntu 26.04 LTS VM set up (VirtualBox, 4 CPU / 12GB RAM / 50GB disk)
- [x] Git + SSH configured, GitHub repo created
- [x] Docker installed
- [x] Python environment + ML stack installed (scikit-learn, PyTorch, SHAP, Streamlit)
- [ ] CIC-IDS2017 + CIC-IoT2023 downloaded and explored
- [ ] Feature schemas aligned across datasets
- [ ] Class imbalance handled (SMOTE); preprocessing pipeline built
- [ ] Literature review notes compiled (12-15 papers)
- [ ] Baseline Isolation Forest trained
- [ ] One-Class SVM trained

*(Week 2 section will be added once Week 1 wraps up.)*

---

## Setup

*(Fill in once the environment is finalized — commands, dependencies, how to run.)*

## Discoveries & Notes

A running log of things learned, decisions made, and problems solved along the way.

###CIC-IDS2017 Exploration (Day 2)

Explored the schema and label distribution across three days of the CIC-IDS2017 dataset. Key findings:

1. **Schema confirmed**: 79 columns per file, consistent across days (78 flow-level features plus a `Label` column, with a leading space in the column name).
2. **Monday is a clean baseline**: 529,918 rows, 100% BENIGN. No attack traffic present, confirming Monday is the "normal behavior only" reference day.
3. **Tuesday introduces brute-force attacks**: 445,909 rows — 432,074 BENIGN, 7,938 FTP-Patator, 5,897 SSH-Patator. Roughly 97% benign to 3% attack, a realistic imbalance.
4. **Wednesday introduces DoS-family attacks with heavy internal imbalance**: 692,703 rows — 440,031 BENIGN, 231,073 DoS Hulk, 10,293 DoS GoldenEye, 5,796 DoS slowloris, 5,499 DoS Slowhttptest, and only 11 Heartbleed.
5. **Rare-class limitation identified**: With only 11 Heartbleed samples, any recall/precision metric on this class alone will be statistically unreliable. Documented as a known limitation rather than an expected strong result.
6. **Class dominance risk identified**: DoS Hulk makes up roughly a third of Wednesday's total rows. If all days are combined, this subtype could dominate the "attack" class and skew aggregate metrics. Mitigation: report per-class breakdowns alongside aggregate scores.
7. **Labeling strategy confirmed**: All non-BENIGN labels will be collapsed into a single ANOMALY class, consistent with the unsupervised approach (Isolation Forest, Autoencoder) rather than multi-class supervised classification.
### CIC-IDS2017 Preprocessing Pipeline (Day 2-3)

Combined all 8 daily CSV files into a single dataset and applied cleaning steps:
1. Combined shape: 2,830,743 rows, 79 columns across all 8 days.
2. Column names stripped of leading whitespace for consistency (e.g. ' Label' became 'Label').
3. Binary label created (BENIGN = 0, ANOMALY = 1). Overall split: 2,273,097 benign (80.3%) vs 557,646 anomalous (19.7%) — a more balanced ratio than any single day alone.
4. Infinite values found in rate-based columns (Flow Bytes/s, Flow Packets/s), caused by zero-duration flows creating division-by-zero. Converted to NaN and dropped: 2,867 rows removed (0.1%).
5. Duplicate rows identified: 307,078 (10.9% of the dataset), a known characteristic of CIC-IDS2017. Removed via drop_duplicates.
6. Final cleaned dataset: 2,520,798 rows, 80 columns, saved as cicids2017_cleaned.csv (excluded from Git via .gitignore, regeneratable from raw data + this pipeline).

## Date
- **[08/08/2026]**  

