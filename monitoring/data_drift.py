import pandas as pd
import numpy as np
import logging
from scipy.stats import ks_2samp
import os
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw/PS_20174392719_1491204439457_log.csv'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/audit_log.db'))

def check_data_drift(reference_df, current_df, features, threshold=0.05):
    """
    Perform Kolmogorov-Smirnov test on continuous features to detect drift.
    A p-value < threshold indicates significant drift.
    """
    drift_detected = False
    drift_report = {}
    
    for feature in features:
        if feature in reference_df.columns and feature in current_df.columns:
            stat, p_value = ks_2samp(reference_df[feature].dropna(), current_df[feature].dropna())
            if p_value < threshold:
                drift_detected = True
                status = "DRIFT"
            else:
                status = "STABLE"
                
            drift_report[feature] = {"p_value": p_value, "status": status}
    
    return drift_detected, drift_report

def main():
    logger.info("Starting Data Drift Monitor...")
    if not os.path.exists(DATA_PATH):
        logger.error("Reference dataset not found.")
        return
        
    if not os.path.exists(DB_PATH):
        logger.error("Audit Database not found. Cannot check for drift without live data.")
        return
        
    logger.info("Loading reference dataset...")
    # Load just a sample to save memory during monitoring
    reference_df = pd.read_csv(DATA_PATH, nrows=50000)
    
    logger.info("Loading current live data from Audit Log...")
    conn = sqlite3.connect(DB_PATH)
    current_df = pd.read_sql_query("SELECT * FROM transaction_audit_logs", conn)
    conn.close()
    
    if len(current_df) < 100:
        logger.info("Not enough live data in Audit Log to perform a reliable drift test (Need at least 100). Current: %d", len(current_df))
        return
        
    features_to_monitor = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    
    logger.info("Running KS-Test for drift detection on features: %s", features_to_monitor)
    drift, report = check_data_drift(reference_df, current_df, features_to_monitor)
    
    for feature, result in report.items():
        if result['status'] == 'DRIFT':
            logger.warning(f"Feature '{feature}' shows DRIFT! (p-value: {result['p_value']:.4e})")
        else:
            logger.info(f"Feature '{feature}' is STABLE. (p-value: {result['p_value']:.4e})")
            
    if drift:
        logger.warning("🚨 DATA DRIFT DETECTED. Model retraining may be required.")
    else:
        logger.info("✅ No significant data drift detected.")

if __name__ == "__main__":
    main()
