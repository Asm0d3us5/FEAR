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

