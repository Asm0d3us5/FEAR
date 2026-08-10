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
- [x] CIC-IDS2017 + CIC-IoT2023 downloaded and explored
- [x] Feature schemas aligned across datasets
- [ ] Class imbalance handled (SMOTE); preprocessing pipeline built
- [ ] Literature review notes compiled (12-15 papers)
- [x] Baseline Isolation Forest trained
- [x] One-Class SVM trained

*(Week 2 section will be added once Week 1 wraps up.)*

---

## Setup

*(Fill in once the environment is finalized — commands, dependencies, how to run.)*

## Discoveries & Notes

A running log of things learned, decisions made, and problems solved along the way.

### CIC-IDS2017 Exploration (Day 2)

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
3. Binary label created (BENIGN = 0, ANOMALY = 1). Overall split: 2,273,097 benign (80.3%) vs 557,646 anomalous (19.7%) a more balanced ratio than any single day alone.
4. Infinite values found in rate-based columns (Flow Bytes/s, Flow Packets/s), caused by zero-duration flows creating division-by-zero. Converted to NaN and dropped: 2,867 rows removed (0.1%).
5. Duplicate rows identified: 307,078 (10.9% of the dataset), a known characteristic of CIC-IDS2017. Removed via drop_duplicates.
6. Final cleaned dataset: 2,520,798 rows, 80 columns, saved as cicids2017_cleaned.csv (excluded from Git via .gitignore, regeneratable from raw data + this pipeline).

### Isolation Forest Baseline (Day 3)

Trained the first baseline model on the cleaned CIC-IDS2017 dataset (2,520,798 rows, 70/30 train/test split, stratified).

1. **Initial result (raw features, contamination=0.2)**: 91% precision / 87% recall on BENIGN, but only 47% precision / 55% recall on ANOMALY. Overall accuracy 82%, but accuracy is misleading here given the class imbalance the anomaly class performance is the real measure of usefulness.
2. **Feature scaling tested**: applied StandardScaler and retrained. Result was nearly identical (47% precision / 55% recall, unchanged). This confirms Isolation Forest is scale-invariant by design, since it partitions data via tree splits on raw values rather than measuring distances between points. Scaling is expected to matter more for distance-based methods like One-Class SVM, tested next.
3. **Precision-recall tradeoff analysis**: plotted precision and recall against decision function threshold. The curves cross near threshold 0 (the current default operating point), with precision peaking around 50% and recall around 55-60% in the same region. Past threshold ~0.15, both collapse toward zero, confirming there is no hidden better operating point being missed at the default settings, this is roughly Isolation Forest's ceiling on raw, untransformed features.
4. **Design decision**: since this is a forensic tool, recall (catching real attacks) is prioritized over precision (avoiding false alarms), a missed attack is a more costly error than an alert an analyst has to dismiss. A higher-recall operating point (~60-65% recall, ~40% precision) is the more defensible choice for this use case.
5. **Sets up the model comparison**: this ~50% precision ceiling on Isolation Forest is a useful benchmark. If One-Class SVM or the Autoencoder clear this ceiling, that's a genuine finding.

### One-Class SVM Baseline (Day 3)

Trained on a 50,000-row stratified sample (full dataset infeasible for One-Class SVM's computational complexity).
1. Result: 37% precision / 44% recall on ANOMALY class (vs Isolation Forest's 47%/55% on the full dataset).
2. Isolation Forest outperforms One-Class SVM on every metric while also scaling to the full 2.5M-row dataset, whereas One-Class SVM required sampling to just 50K rows (2%) to remain computationally feasible.
3. This is a meaningful comparative finding: model choice for forensic tooling must weigh not just detection performance but computational scalability to production-sized traffic volumes.

### Autoencoder — Technical Notes (Day 4)

1. **Training approach differs from the other two models**: unlike Isolation Forest and One-Class SVM (trained on the full mixed benign+anomaly training set), the Autoencoder was trained exclusively on benign rows. This is the standard approach for autoencoder-based anomaly detection the model learns to reconstruct "normal" patterns well, and poor reconstruction on unseen data becomes the anomaly signal itself, rather than a learned decision boundary.
2. **Architecture**: a 3-layer encoder (78 → 32 → 16 → 8) and mirrored 3-layer decoder (8 → 16 → 32 → 78), using ReLU activations and MSE loss. The 8-dimensional bottleneck forces the model to retain only the most essential patterns of normal traffic, discarding noise.
3. **Training behaviour**: loss decreased steadily and consistently across all 20 epochs (0.2957 → 0.0778), with no signs of instability or overfitting oscillation, indicating the architecture and learning rate (0.001, Adam optimiser) were well-suited to this data without needing further tuning for a first pass.
4. **Threshold selection**: rather than using a fixed model output like Isolation Forest/SVM's -1/1 predictions, the Autoencoder requires choosing a reconstruction error cutoff. The 80th percentile of benign reconstruction error was used as the threshold (flagging the "worst-reconstructed" 20% of test data as anomalous) this is a tunable parameter that directly trades precision against recall, and was not exhaustively optimised in this first pass.
5. **Reconstruction error visualisation confirmed genuine learned separation**: benign flows cluster tightly near-zero error on a log-scale histogram, while anomalous flows show a distinct, persistent tail extending to much higher error values (up to ~2.0), rather than the two distributions being indistinguishable.
6. **Computational trade-off**: training took ~225 seconds on the full ~2M-row benign training set notably slower than Isolation Forest (~9 sec) but still practical for a one-time training pass, especially given the strong 82% recall achieved.

### Three-Model Comparison (Day 4)

| Model | Precision (Anomaly) | Recall (Anomaly) | F1-score | Training Data | Training Time |
|---|---|---|---|---|---|
| Isolation Forest | 47% | 55% | 51% | Full 2.5M rows | ~9 sec |
| One-Class SVM | 37% | 44% | 40% | Sampled 50K rows (2%) | ~37 sec |
| Autoencoder | 46% | 82% | 59% | Full 2.5M benign rows | ~225 sec |

1. **Autoencoder is the leading model**, achieving substantially higher recall (82%) and F1-score (59%) than both other models, while matching Isolation Forest's precision (~46-47%).
2. **Reconstruction error visualization confirms genuine separation**: benign flows cluster tightly near-zero error, while anomalous flows show a distinct, persistent tail extending to much higher reconstruction error, visually validating the model learned meaningful patterns of normal behaviour.
3. **Design rationale reinforced**: since forensic use prioritizes recall (catching real attacks) over precision, the Autoencoder's 82% recall makes it the strongest candidate to carry forward into cross-dataset generalization testing (CIC-IoT2023) and SHAP explainability in later weeks.
4. **Trade-off noted**: the Autoencoder took the longest to train (~225 seconds vs Isolation Forest's ~9 seconds), a reasonable cost given the significant performance gain, but worth stating explicitly as a resource trade-off in the final report.


## Date
- **[08/08/2026]**  
- **[10/08/2026]**  

