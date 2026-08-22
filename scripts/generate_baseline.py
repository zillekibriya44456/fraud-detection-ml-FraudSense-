import pandas as pd
import numpy as np
import json
import os
import logging
import sys

# Ensure modules can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.preprocessing import load_and_clean_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw/PS_20174392719_1491204439457_log.csv'))
ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../artifacts'))
BASELINE_PATH = os.path.join(ARTIFACT_DIR, 'drift_baseline_v1.json')

def compute_numerical_baseline(series, num_bins=10):
    # Using quantiles for robust binning
    quantiles = np.linspace(0, 1, num_bins + 1)
    bins = series.quantile(quantiles).values
    
    # Ensure bins are unique (handle heavily skewed distributions where e.g., 20% of data is 0)
    bins = np.unique(bins)
    if len(bins) < 2:
        bins = np.array([series.min(), series.max() + 1e-9])
        
    counts, edges = np.histogram(series, bins=bins)
    
    # Normalize to probabilities
    probs = counts / counts.sum()
    
    # Avoid zero probabilities for PSI calculations later
    probs = np.clip(probs, a_min=1e-5, a_max=None)
    probs = probs / probs.sum()
    
    return {
        "mean": float(series.mean()),
        "std": float(series.std()),
        "min": float(series.min()),
        "max": float(series.max()),
        "bins": edges.tolist(),
        "probabilities": probs.tolist()
    }

def compute_categorical_baseline(series):
    counts = series.value_counts(normalize=True)
    
    # Avoid zero probabilities
    probs = counts.to_dict()
    
    return {
        "probabilities": probs
    }

def main():
    logger.info("Loading training dataset from %s", DATA_PATH)
    if not os.path.exists(DATA_PATH):
        logger.error("Dataset not found!")
        return

    df = load_and_clean_data(DATA_PATH)
    
    baseline = {
        "metadata": {
            "version": "v1.0",
            "dataset": "PS_20174392719_1491204439457_log.csv",
            "sample_size": len(df),
            "created_at": pd.Timestamp.utcnow().isoformat()
        },
        "features": {
            "numerical": {},
            "categorical": {}
        }
    }
    
    logger.info("Computing baselines for numerical features...")
    numerical_features = ["amount", "oldbalanceOrg", "oldbalanceDest"]
    for feat in numerical_features:
        if feat in df.columns:
            logger.info(f"Processing {feat}")
            baseline["features"]["numerical"][feat] = compute_numerical_baseline(df[feat])
            
    logger.info("Computing baselines for categorical features...")
    categorical_features = ["type"]
    for feat in categorical_features:
        if feat in df.columns:
            logger.info(f"Processing {feat}")
            baseline["features"]["categorical"][feat] = compute_categorical_baseline(df[feat])
            
    # Also create a baseline for fraud probability. Since we don't have predictions on the raw data readily available, 
    # we simulate the expected output distribution (heavily skewed to 0) based on target labels.
    # We will use the target variable 'isFraud' as a proxy for probability distributions for the baseline.
    logger.info("Computing baseline for expected prediction probability...")
    if "isFraud" in df.columns:
        # Realistic probabilities would cluster near 0 for legitimate, and near 1 for fraud.
        simulated_probs = np.where(df["isFraud"] == 1, 
                                 np.random.uniform(0.8, 1.0, len(df)), 
                                 np.random.uniform(0.0, 0.2, len(df)))
        baseline["features"]["prediction"] = compute_numerical_baseline(pd.Series(simulated_probs))

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(BASELINE_PATH, 'w') as f:
        json.dump(baseline, f, indent=4)
        
    logger.info("Baseline saved to %s", BASELINE_PATH)

if __name__ == "__main__":
    main()
