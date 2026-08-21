# FEAR — Flow-based Explainable Anomaly Recognition

A hybrid unsupervised machine learning framework for flow-based, explainable anomaly detection in encrypted network traffic.

**Core idea:** detect suspicious network activity using only flow-level metadata (packet size, timing, direction) — no payload decryption required.

Full technical findings and discovery log: [docs/findings.md](docs/findings.md)

---

## Progress Tracker

### Week 1 — Foundation & Data ✅
- [x] Ubuntu 26.04 LTS VM, Git/SSH/GitHub, Docker, Python/ML stack
- [x] CIC-IDS2017 + CIC-IoT2023 downloaded and explored
- [x] Preprocessing pipeline built (combined, cleaned, binary-labeled)
- [x] Three baseline models trained and compared (Isolation Forest, One-Class SVM, Autoencoder)
- [x] Per-attack-type recall breakdown across all models
- [x] SMOTE tested and rejected (evidence-based decision)
- [x] Literature review (5 papers)

### Week 2 — Model Development ✅
- [x] Autoencoder tuned and confirmed as leading model
- [x] Cross-dataset generalization test (CIC-IDS2017 → CIC-IoT2023)
- [x] Domain shift diagnosed and confirmed via recalibration test

### Week 3 — Explainability, Robustness, Tooling (in progress)
- [ ] SHAP explainability
- [ ] Adversarial evasion testing
- [ ] Streamlit dashboard

### Week 4 — Packaging & Reporting
- [ ] Dockerize pipeline
- [ ] README/architecture diagram, demo video
- [ ] Final report write-up and submission

---

## Setup

*(Fill in once the environment is finalized — commands, dependencies, how to run.)*

## Results Summary

| Model | Precision (Anomaly) | Recall (Anomaly) | F1-score | Training Data | Training Time |
|---|---|---|---|---|---|
| Isolation Forest | 47% | 55% | 51% | Full 2.5M rows | ~9 sec |
| One-Class SVM (RBF, sampled) | 37% | 44% | 40% | 50K rows (2%) | ~37 sec |
| One-Class SVM (SGD, full data) | 15% | 3% | 4% | Full 2.5M rows | fast |
| **Autoencoder (leading model)** | **46%** | **82%** | **59%** | Full 2.5M benign rows | ~225 sec |

**Leading model:** Autoencoder, selected for its substantially higher recall — the priority metric for forensic use, where missing an attack costs more than a false alarm.

See [docs/findings.md](docs/findings.md) for per-attack-type breakdowns, the cross-dataset generalization result, and full reasoning behind each design decision.




