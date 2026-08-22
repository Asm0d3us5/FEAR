from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
CICIDS2017_CLEANED = DATA_DIR / "cicids2017_cleaned.csv"
AUTOENCODER_PATH = MODELS_DIR / "autoencoder.pt"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
FLAGGED_RESULTS_PATH = DASHBOARD_DIR / "flagged_results.csv"
SHAP_VALUES_PATH = DASHBOARD_DIR / "shap_values.csv"
