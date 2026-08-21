FEAR — Detailed Findings & Discoveries

Full technical log of exploration, decisions, and results. Organized by week.

Week 1 — Foundation & Data
CIC-IDS2017 Exploration (Day 2)

Explored the schema and label distribution across three days of the CIC-IDS2017 dataset.

Schema confirmed: 79 columns per file, consistent across days (78 flow-level features plus a Label column, with a leading space in the column name).
Monday is a clean baseline: 529,918 rows, 100% BENIGN. No attack traffic present, confirming Monday is the "normal behavior only" reference day.
Tuesday introduces brute-force attacks: 445,909 rows — 432,074 BENIGN, 7,938 FTP-Patator, 5,897 SSH-Patator. Roughly 97% benign to 3% attack, a realistic imbalance.
Wednesday introduces DoS-family attacks with heavy internal imbalance: 692,703 rows — 440,031 BENIGN, 231,073 DoS Hulk, 10,293 DoS GoldenEye, 5,796 DoS slowloris, 5,499 DoS Slowhttptest, and only 11 Heartbleed.
Rare-class limitation identified: with only 11 Heartbleed samples, any recall/precision metric on this class alone will be statistically unreliable. Documented as a known limitation rather than an expected strong result.
Class dominance risk identified: DoS Hulk makes up roughly a third of Wednesday's total rows. If all days are combined, this subtype could dominate the "attack" class and skew aggregate metrics. Mitigation: report per-class breakdowns alongside aggregate scores.
Labeling strategy confirmed: all non-BENIGN labels will be collapsed into a single ANOMALY class, consistent with the unsupervised approach (Isolation Forest, Autoencoder) rather than multi-class supervised classification.
CIC-IDS2017 Preprocessing Pipeline (Day 2-3)

Combined all 8 daily CSV files into a single dataset and applied cleaning steps:

Combined shape: 2,830,743 rows, 79 columns across all 8 days.
Column names stripped of leading whitespace for consistency (e.g. ' Label' became 'Label').
Binary label created (BENIGN = 0, ANOMALY = 1). Overall split: 2,273,097 benign (80.3%) vs 557,646 anomalous (19.7%), a more balanced ratio than any single day alone.
Infinite values found in rate-based columns (Flow Bytes/s, Flow Packets/s), caused by zero-duration flows creating division-by-zero. Converted to NaN and dropped: 2,867 rows removed (0.1%).
Duplicate rows identified: 307,078 (10.9% of the dataset), a known characteristic of CIC-IDS2017. Removed via drop_duplicates.
Final cleaned dataset: 2,520,798 rows, 80 columns, saved as cicids2017_cleaned.csv (excluded from Git via .gitignore, regeneratable from raw data + this pipeline).
Isolation Forest Baseline (Day 3)

Trained the first baseline model on the cleaned CIC-IDS2017 dataset (2,520,798 rows, 70/30 train/test split, stratified).

Initial result (raw features, contamination=0.2): 91% precision / 87% recall on BENIGN, but only 47% precision / 55% recall on ANOMALY. Overall accuracy 82%, but accuracy is misleading given the class imbalance — anomaly class performance is the real measure of usefulness.
Feature scaling tested: applied StandardScaler and retrained. Result was nearly identical (47%/55%, unchanged). Confirms Isolation Forest is scale-invariant by design, since it partitions data via tree splits on raw values rather than measuring distances between points.
Precision-recall tradeoff analysis: plotted precision and recall against decision function threshold. The curves cross near threshold 0 (the default operating point), with precision peaking around 50% and recall around 55-60% in the same region. Past threshold ~0.15, both collapse toward zero — no hidden better operating point at default settings.
Design decision: since this is a forensic tool, recall (catching real attacks) is prioritized over precision (avoiding false alarms) — a missed attack is a more costly error than a dismissible alert. A higher-recall operating point (~60-65% recall, ~40% precision) is the more defensible choice.
Sets up the model comparison: this ~50% precision ceiling is a useful benchmark for evaluating the other two models.
One-Class SVM Baseline (Day 3)

Trained on a 50,000-row stratified sample (full dataset infeasible for One-Class SVM's computational complexity).

Result: 37% precision / 44% recall on ANOMALY class (vs Isolation Forest's 47%/55% on the full dataset).
Isolation Forest outperforms One-Class SVM on every metric while also scaling to the full 2.5M-row dataset, whereas One-Class SVM required sampling to just 50K rows (2%) to remain computationally feasible.
Meaningful comparative finding: model choice for forensic tooling must weigh not just detection performance but computational scalability to production-sized traffic volumes.
Autoencoder — Technical Notes (Day 4)
Training approach differs from the other two models: trained exclusively on benign rows, the standard approach for autoencoder-based anomaly detection — the model learns to reconstruct "normal" patterns well, and poor reconstruction becomes the anomaly signal itself.
Architecture: 3-layer encoder (78 → 32 → 16 → 8) and mirrored 3-layer decoder (8 → 16 → 32 → 78), ReLU activations, MSE loss. The 8-dimensional bottleneck forces the model to retain only the most essential patterns of normal traffic.
Training behaviour: loss decreased steadily across all 20 epochs (0.2957 → 0.0778), no instability, indicating the architecture and learning rate (0.001, Adam) suited the data well.
Threshold selection: the 80th percentile of benign reconstruction error was used as the threshold (flagging the worst-reconstructed 20% as anomalous) — a tunable parameter trading precision against recall, not exhaustively optimised in this first pass.
Reconstruction error visualisation confirmed genuine learned separation: benign flows cluster tightly near-zero error, while anomalous flows show a distinct, persistent tail extending to much higher error (up to ~2.0).
Computational trade-off: training took ~225 seconds — slower than Isolation Forest (~9 sec) but practical given the strong 82% recall achieved.
Three-Model Comparison (Day 4)
Model	Precision (Anomaly)	Recall (Anomaly)	F1-score	Training Data	Training Time
Isolation Forest	47%	55%	51%	Full 2.5M rows	~9 sec
One-Class SVM	37%	44%	40%	Sampled 50K rows (2%)	~37 sec
Autoencoder	46%	82%	59%	Full 2.5M benign rows	~225 sec
Autoencoder is the leading model, achieving substantially higher recall (82%) and F1-score (59%) than both other models, while matching Isolation Forest's precision.
Reconstruction error visualization confirms genuine separation between benign and anomalous flows, visually validating the model learned meaningful patterns of normal behaviour.
Design rationale reinforced: recall matters most for forensic use, making the Autoencoder the strongest candidate to carry forward.
Trade-off noted: longest training time of the three, a reasonable cost given the performance gain — worth stating explicitly as a resource trade-off in the final report.
Per-Attack-Type Recall Breakdown — Autoencoder (Day 5)

Checked recall for each specific attack type rather than relying on aggregate ANOMALY recall (82%), which was masking major differences.

Strong detection (92-99% recall): DoS Hulk, DoS GoldenEye, DoS Slowhttptest, Infiltration. Flow-level features clearly capture volumetric/timing signatures.
Heartbleed: 100% recall, but on only 11 samples — a single misclassification would drop this to ~91%. Reported with this caveat rather than as a robust guarantee.
Critical weakness identified and verified: SSH-Patator (0.6% recall) and FTP-Patator (0.9% recall) are almost completely undetected. Direct comparison of flow-level statistics confirms this is not a data quality or sample-size artefact: FTP-Patator's mean Total Fwd Packets (11.2) is nearly identical to BENIGN traffic (11.4), and Flow Duration falls well within BENIGN's normal range. The attack signature is not visible at the single-flow level — it only emerges from the pattern of many similar-looking flows occurring in rapid succession, which per-flow feature analysis structurally cannot capture.
Reframes the project's limitations section: flow-level anomaly detection excels at volumetric/single-flow-anomalous attacks but requires a different approach (e.g. session/time-window aggregation features) to catch behaviorally-distributed attacks like brute force. Named explicitly as future work.
One-Class SVM: Full-Data Fairness Check (SGDOneClassSVM)

Addressed the concern that the original kernel SVM result (37%/44%) might be an artefact of the 50,000-row sample rather than a genuine model limitation, given kernel SVM's roughly quadratic-to-cubic time complexity makes full-dataset training infeasible.

Tested SGDOneClassSVM, a linear-time approximation capable of training on the full 2,520,798-row dataset.
Result: 15% precision / 3% recall — substantially worse than the sampled kernel SVM, despite 50x more training data.
Conclusion: the kernel SVM's non-linear RBF decision boundary is doing genuine work a linear boundary cannot replicate, even with far more data. This confirms the original sampled result reflects a real algorithmic limitation, not primarily a consequence of insufficient training data. Kernel SVM (sampled) remains the stronger SVM variant, but both are outperformed by Isolation Forest and the Autoencoder.
Per-Attack-Type Recall — 3-Model Comparison (Day 5-6)

Ran the same per-attack-type breakdown across all three models to check whether the brute-force blind spot was model-specific or a structural limitation of flow-level features.

Confirmed across all three independently-designed algorithms: SSH-Patator, FTP-Patator, Web Attack-XSS, and Bot are near-universally missed (0-9% recall across all models), while volumetric attacks (47-99% recall) and Heartbleed (100% where present in the test set) are consistently well-detected.
Strengthens the earlier finding: since three structurally different algorithms (reconstruction-based, boundary-based, tree-based) independently show the same blind spot, this is strong evidence the limitation is inherent to flow-level, single-flow feature analysis.
Notable disagreement: SQL Injection was caught well by the Autoencoder (71.4%) but completely missed by Isolation Forest (0%) — an example of inter-model disagreement carrying forensic signal.
Sampling consequence confirmed: the kernel SVM's 50,000-row sample did not include any Heartbleed, SQL Injection, or Infiltration rows at all.
SMOTE / Class Imbalance — Tested and Rejected

Reasoned that SMOTE is a poor fit for FEAR's unsupervised models, then tested empirically to confirm.

Rationale: SMOTE balances classes for supervised classifiers. FEAR's three models are all unsupervised and depend on the anomaly class being rare/different from normal traffic — none learn from a "minority class" the way SMOTE assumes.
Empirical test: applied SMOTE to Isolation Forest's training data and retrained.
              precision    recall  f1-score   support
           0       0.86      0.87      0.86    628518
           1       0.30      0.27      0.29    127722
    accuracy                           0.77    756240

Result: precision dropped from 47% to 30%, recall from 55% to 27%, F1 from 51% to 29% — a clear degradation across every metric.

Conclusion: SMOTE is not used in FEAR's final pipeline. A deliberate, evidence-based design decision, documented with the supporting test.
Week 2 — Model Development
Cross-Dataset Generalization Test — CIC-IDS2017 → CIC-IoT2023 (Day 1)

Tested whether an Autoencoder trained on CIC-IDS2017 generalizes to CIC-IoT2023, a structurally different dataset (IoT device traffic vs enterprise/PC traffic).

Schema incompatibility discovered first: CIC-IDS2017 (78 features, bidirectional flow statistics) and CIC-IoT2023 (39 features, packet-header/protocol-flag statistics) share only ~12 directly comparable features (flag counts, packet length stats, IAT mean). A reduced-feature Autoencoder (12 → 8 → 4 → 8 → 12) was trained on CIC-IDS2017 to enable a fair test.
Reduced model outperformed the full 78-feature model on its home dataset: 47% precision / 88% recall vs the original's 46%/82%, suggesting the smaller feature set may carry a higher concentration of genuinely useful anomaly signal.
Generalization failed on CIC-IoT2023: applying the same model, scaler, and threshold (no refitting) resulted in a near-total breakdown:
[[  4346 601614]
 [     6 514939]]
              precision    recall  f1-score   support
           0       1.00      0.01      0.01    605960
           1       0.46      1.00      0.63    514945
    accuracy                           0.46   1120905

99.99% of genuinely benign IoT2023 traffic was misclassified as anomalous (601,614 of 605,960 benign flows flagged).

Root cause confirmed via reconstruction error distribution: CIC-IDS2017's benign traffic clusters tightly near zero reconstruction error, while CIC-IoT2023's benign traffic is spread broadly across the entire error range, overlapping heavily with where CIC-IDS2017's attacks would be expected to fall. This is domain shift: IoT device traffic (small, frequent, repetitive packets from sensors and cameras) is statistically unlike enterprise/PC traffic, so a threshold calibrated on one environment's notion of "normal" does not transfer to the other.
Recalibration test (threshold retuned to IoT2023's own benign distribution, rather than reused from CIC-IDS2017):
Original threshold: 0.0255
Recalibrated threshold: 4.6062
[[484962 120998]
 [486253  28692]]
              precision    recall  f1-score   support
           0       0.50      0.80      0.61    605960
           1       0.19      0.06      0.09    514945
    accuracy                           0.46   1120905

Rather than improving results, recalibration made anomaly detection substantially worse (recall dropped from 100% to 6%, precision from 46% to 19%). This is a stronger, more conclusive finding than a simple threshold-mismatch: it shows the model's underlying reconstruction-error representation does not meaningfully separate benign from anomalous traffic within the IoT2023 domain at all — not just that the wrong cutoff value was used. This rules out a lightweight recalibration fix and confirms that genuine cross-domain deployment would require retraining on domain-representative data, not just threshold adjustment.

This is a substantive, reportable finding, not a failed experiment: it demonstrates that unsupervised anomaly detection models are domain-specific by nature, and that genuine cross-environment deployment requires either domain-specific retraining or a domain-adaptation technique, neither of which was in scope for this project. Directly informs the Limitations and Future Work sections.
Week 3 — Explainability, Robustness, Tooling

### SHAP Explainability — Global Feature Importance (Week 3, Day 1)

Applied SHAP GradientExplainer to the Autoencoder (wrapped to output reconstruction error), explaining 20 correctly-flagged anomalous flows.

1. **Top drivers**: Packet Length Variance, FIN Flag Count, and Bwd Packet Length Std dominate the model's anomaly scoring — high values in these three features consistently push flows toward being flagged as anomalous.
2. **Most of the 78 features contribute minimally** to these specific predictions, indicating the model has effectively learned to concentrate on a small set of structurally meaningful signals (packet size irregularity, flag behavior) rather than spreading importance evenly.
3. **Interpretation**: the model appears to detect anomalies primarily through structural irregularity in traffic (inconsistent packet sizing, unusual flag patterns) rather than simple volume-based signals, supporting the forensic value of this approach — an analyst could investigate flagged flows starting from these specific features rather than reviewing all 78 in isolation.

### SHAP Explainability — Local & Summary Visualizations (Week 3, Day 1)

Generated three complementary SHAP visualizations to explain the Autoencoder's anomaly scoring, all converging on the same top features (Packet Length Variance, FIN Flag Count, Bwd Packet Length Std).

1. **Waterfall plot (single flow, score 8.675)**: demonstrates that individual flagged anomalies can often be explained by a small number of dominant features — in this example, Packet Length Variance alone contributed +7.61 of the total 8.675 score, with 64 other features contributing negligibly. This supports the forensic value of the explainability layer: an analyst can identify the specific behavioral driver behind a flag rather than treating it as an opaque score.
2. **Bar chart (mean absolute SHAP value, top 15 features)**: confirms the beeswarm and waterfall findings with a clean, report-ready ranking — Packet Length Variance, FIN Flag Count, and Bwd Packet Length Std are the three dominant drivers across sampled anomalies.
3. **Cross-method consistency**: all three visualization approaches (beeswarm, waterfall, bar) independently converge on the same top three features, providing internal validation that this is a genuine, stable pattern rather than an artefact of any single plotting method.

### Adversarial Robustness Testing (Week 3, Day 2)

Tested whether the Autoencoder can be evaded by an attacker deliberately perturbing traffic to appear benign, using SHAP-informed targeted attacks and random-noise baselines.

1. **Targeted attack** (perturbing only the top 3 SHAP-identified features, 80% toward benign mean): reduced mean reconstruction error by 69% (2.37 → 0.73), but this remained ~24x above the detection threshold. 0% evasion rate across 2,000 attacked flows.
2. **Escalated targeted attack** (top 10 features, full replacement with benign mean values): still 0% evasion.
3. **Random noise attacks** (all 78 features, scales 0.5 to 5.0): negligible effect on detection, 0% evasion at all tested scales — confirms that untargeted perturbation is an ineffective evasion strategy against this model.
4. **Theoretical ceiling test** (all 78 features fully replaced with the benign-average vector): still scored above threshold (0.0416 vs threshold 0.0298), and still detected.
5. **Root cause identified**: the detection threshold (80th percentile of benign reconstruction error) is aggressive by design, a deliberate Week 1 choice prioritizing recall for forensic use. As a direct consequence, even the average benign flow (error 0.0470) sits above this threshold, meaning roughly 20% of genuinely normal traffic already scores as "anomalous" under this calibration. This makes the bar for successful evasion very high, since an attacker must produce traffic statistically more "normal-looking" than a large fraction of real normal traffic itself.
6. **Trade-off made explicit**: this robustness is not free. The same aggressive threshold that resists evasion is also directly responsible for the model's imperfect precision on benign traffic (Week 1 results: ~91-97% precision on BENIGN, meaning some real benign flows are already flagged). Adversarial resistance and false-positive rate are in direct tension at this threshold setting, a genuine design trade-off rather than an unqualified strength.
7. **Conclusion**: within the perturbation strategies tested, the model resisted evasion, but this reflects a conservative threshold calibration rather than the model being inherently unbeatable. A more permissive, higher-precision threshold would likely also be more vulnerable to targeted evasion, a relationship worth stating explicitly as a limitation and an avenue for future adversarial training work.

### Gradient-Based Adversarial Attack (Week 3, Day 2, continued)

Escalated robustness testing with an unconstrained white-box gradient attack — using the model's own gradients to find the mathematically optimal perturbation minimizing reconstruction error, rather than a heuristic-guided attack.

1. **Result**: 700 of 2,000 attacked flows (35.3%) successfully evaded detection, with mean reconstruction error dropping to 0.698 (still above the original benign mean, but below threshold for over a third of samples).
2. **This is the expected and informative outcome**: unlike the heuristic attacks (SHAP-targeted, random noise, full replacement), all of which achieved 0% evasion, a full white-box gradient attack represents the theoretical ceiling of attacker capability, assuming complete access to model internals. Finding a real, non-trivial evasion rate only at this threat level, rather than at every threat level, indicates the earlier 0% results reflect genuine robustness against realistic attackers rather than an insufficiently rigorous test.
3. **Threat model caveat**: this attack assumes white-box access (full knowledge of model weights and architecture), which is a strong, often unrealistic assumption for a real-world attacker without insider access. It represents a worst-case bound, not an expected real-world evasion rate.
4. **Conclusion**: FEAR's Autoencoder demonstrates strong practical robustness against realistic evasion strategies (naive and semi-informed attackers), but retains a quantifiable vulnerability (35.3% evasion rate) against a sophisticated, fully-informed adversary. This is a defensible, complete robustness finding: rather than an unqualified claim of resistance, the boundary between "robust" and "vulnerable" is precisely characterized by attacker capability level, directly supporting future work in adversarial training or ensemble-based defenses.

(To be added as work progresses.)

Week 4 — Packaging & Reporting

(To be added as work progresses.)

Session Dates
08/08/2026
10/08/2026
14/08/2026
15/08/2026
