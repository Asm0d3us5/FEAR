import streamlit as st
import pandas as pd

st.set_page_config(page_title="FEAR Dashboard", layout="wide")

st.title("FEAR — Flow-based Explainable Anomaly Recognition")
st.markdown("*A hybrid unsupervised ML framework for flow-based anomaly detection in encrypted network traffic*")

st.markdown("---")

st.header("Project Overview")
st.write("""
FEAR detects suspicious network activity using only flow-level metadata 
(packet size, timing, direction), no payload decryption required. 
Built and evaluated on CIC-IDS2017. Cross-dataset generalization testing 
on CIC-IoT2023 revealed significant domain shift between enterprise and 
IoT traffic, a key finding detailed in the Limitations section.
""")

st.header("Model Comparison")

comparison_data = {
    "Model": ["Isolation Forest", "One-Class SVM", "Autoencoder (leading model)"],
    "Precision (Anomaly)": ["47%", "37%", "46%"],
    "Recall (Anomaly)": ["55%", "44%", "82%"],
    "F1-score": ["51%", "40%", "59%"],
    "Training Data": ["Full 2.5M rows", "Sampled 50K rows", "Full 2.5M benign rows"],
    "Training Time": ["~9 sec", "~37 sec", "~225 sec"],
}
df_comparison = pd.DataFrame(comparison_data)
st.dataframe(df_comparison, use_container_width=True)

st.markdown("**Leading model:** Autoencoder selected for its substantially higher recall, the priority metric for forensic use where missing an attack costs more than a false alarm.")

st.markdown("---")
st.header("Flagged Flows")

results = pd.read_csv("flagged_results.csv")

status_filter = st.selectbox(
    "Filter by outcome",
    ["All", "Correctly detected anomalies", "Missed anomalies", "Benign flows"]
)

if status_filter == "Correctly detected anomalies":
    display_df = results[(results['true_label']==1) & (results['predicted_anomaly']==1)]
elif status_filter == "Missed anomalies":
    display_df = results[(results['true_label']==1) & (results['predicted_anomaly']==0)]
elif status_filter == "Benign flows":
    display_df = results[results['true_label']==0]
else:
    display_df = results

st.write(f"Showing {len(display_df)} flows")
st.dataframe(
    display_df[['original_label', 'anomaly_score', 'predicted_anomaly', 'true_label']],
    use_container_width=True
)

st.markdown("---")
st.header("Explain a Flow")

shap_values = pd.read_csv("shap_values.csv")
feature_cols = [c for c in results.columns if c not in
                ['true_label', 'anomaly_score', 'predicted_anomaly', 'original_label']]

selected_idx = st.selectbox(
    "Select a flow to explain (index matches the table above)",
    display_df.index.tolist(),
    format_func=lambda i: f"Row {i} — {results.loc[i, 'original_label']} (score: {results.loc[i, 'anomaly_score']:.4f})"
)

st.write(f"**True label:** {results.loc[selected_idx, 'original_label']} | "
         f"**Predicted:** {'Anomaly' if results.loc[selected_idx, 'predicted_anomaly']==1 else 'Benign'} | "
         f"**Anomaly score:** {results.loc[selected_idx, 'anomaly_score']:.4f}")

import matplotlib.pyplot as plt
import shap

row_shap_values = shap_values.loc[selected_idx].values
row_feature_values = results.loc[selected_idx, feature_cols].values

explanation = shap.Explanation(
    values=row_shap_values,
    base_values=shap_values.values.mean(),
    data=row_feature_values,
    feature_names=feature_cols
)

fig, ax = plt.subplots()
shap.plots.waterfall(explanation, max_display=10, show=False)
st.pyplot(fig)

st.markdown("---")
st.header("Robustness & Limitations")

st.subheader("Adversarial Robustness")
st.write("""
Tested how easily the model can be evaded by an attacker deliberately 
perturbing traffic to appear benign.
""")

robustness_data = {
    "Attack Type": ["SHAP-targeted (top 3 features)", "Random noise (all 78 features)",
                     "Full replacement (benign mean)", "Gradient-based (white-box, optimal)"],
    "Threat Model": ["Semi-informed attacker", "Naive attacker",
                      "Naive brute-force", "Sophisticated, full model access"],
    "Evasion Rate": ["0%", "0%", "0%", "35.3%"],
}
st.dataframe(pd.DataFrame(robustness_data), use_container_width=True)
st.caption("The model resists realistic, low-to-medium sophistication attacks, but retains a "
           "quantifiable vulnerability against a fully-informed, white-box adversary.")

st.subheader("Domain Shift — Cross-Dataset Generalization")
st.write("""
An Autoencoder trained on CIC-IDS2017 (enterprise/PC traffic) was tested on 
CIC-IoT2023 (IoT device traffic). Detection broke down almost completely: 
99.99% of genuinely benign IoT traffic was misclassified as anomalous.
""")
st.caption("Root cause: IoT device traffic is statistically unlike enterprise traffic, so a "
           "threshold calibrated on one environment's notion of 'normal' does not transfer. "
           "Confirmed via reconstruction error distribution and a recalibration test that "
           "ruled out a simple threshold fix.")

st.subheader("Known Blind Spot — Brute Force Attacks")
st.write("""
SSH-Patator and FTP-Patator attacks are almost completely undetected 
(0.6% and 0.9% recall respectively) across all three models tested.
""")
st.caption("Confirmed structural, not a data artefact: individual brute-force login flows are "
           "statistically indistinguishable from benign traffic. The attack signature only "
           "emerges from the pattern of many similar flows in rapid succession, which "
           "per-flow feature analysis cannot capture.")

st.markdown("---")
st.caption("FEAR is a validated proof-of-concept for analyst-assisted forensic triage, "
           "not a production-ready autonomous detection system.")
