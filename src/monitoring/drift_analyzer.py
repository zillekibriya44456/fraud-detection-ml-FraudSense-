import yaml
import json
import os
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from database.models import TransactionAuditLog
import logging

logger = logging.getLogger(__name__)

POLICY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/drift_policy.yaml'))
BASELINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../artifacts/drift_baseline_v1.json'))

class DriftAnalyzer:
    def __init__(self):
        self._load_config()
        self._load_baseline()

    def _load_config(self):
        with open(POLICY_PATH, 'r') as file:
            self.config = yaml.safe_load(file)
            self.monitoring = self.config.get('monitoring', {})
            self.window_size = self.monitoring.get('window_size', 1000)
            self.min_sample_size = self.monitoring.get('min_sample_size', 100)
            self.thresholds = self.config.get('drift_thresholds', {})
            self.features = self.config.get('features_monitored', {})

    def _load_baseline(self):
        if os.path.exists(BASELINE_PATH):
            with open(BASELINE_PATH, 'r') as file:
                self.baseline = json.load(file)
        else:
            logger.warning(f"Baseline file {BASELINE_PATH} not found.")
            self.baseline = None

    def calculate_psi(self, expected_probs, actual_probs):
        """Calculate Population Stability Index"""
        def safe_prob(p):
            return np.clip(p, a_min=1e-5, a_max=None)
            
        expected = safe_prob(np.array(expected_probs))
        actual = safe_prob(np.array(actual_probs))
        
        psi = np.sum((actual - expected) * np.log(actual / expected))
        return float(psi)

    def get_severity(self, psi, feature_type="numerical"):
        thresh = self.thresholds.get(f"{feature_type}_psi", {})
        if psi >= thresh.get('high', 0.25):
            return "HIGH"
        elif psi >= thresh.get('medium', 0.2):
            return "MEDIUM"
        elif psi >= thresh.get('low', 0.1):
            return "LOW"
        return "NO_DRIFT"

    def analyze_drift(self, db: Session):
        if not self.baseline:
            return {"status": "ERROR", "detail": "Baseline not found."}

        logs = db.query(TransactionAuditLog).order_by(TransactionAuditLog.timestamp.desc()).limit(self.window_size).all()
        
        if len(logs) < self.min_sample_size:
            return {
                "status": "INSUFFICIENT_DATA",
                "sample_size": len(logs),
                "min_required": self.min_sample_size
            }
            
        df = pd.DataFrame([{
            "amount": log.amount,
            "oldbalanceOrg": log.oldbalanceOrg,
            "oldbalanceDest": log.oldbalanceDest,
            "type": log.type,
            "fraud_probability": log.fraud_probability
        } for log in logs])
        
        results = {
            "status": "SUCCESS",
            "sample_size": len(logs),
            "baseline_version": self.baseline.get("metadata", {}).get("version", "unknown"),
            "features": [],
            "prediction_drift": None
        }
        
        # Analyze Numerical Features
        for feat in self.features.get('numerical', []):
            if feat in df.columns and feat in self.baseline["features"]["numerical"]:
                base = self.baseline["features"]["numerical"][feat]
                bins = base["bins"]
                expected_probs = base["probabilities"]
                
                counts, _ = np.histogram(df[feat], bins=bins)
                actual_probs = counts / counts.sum()
                
                psi = self.calculate_psi(expected_probs, actual_probs)
                severity = self.get_severity(psi, "numerical")
                
                results["features"].append({
                    "feature_name": feat,
                    "type": "numerical",
                    "drift_detected": severity != "NO_DRIFT",
                    "drift_score": psi,
                    "severity": severity
                })
                
        # Analyze Categorical Features
        for feat in self.features.get('categorical', []):
            if feat in df.columns and feat in self.baseline["features"]["categorical"]:
                base = self.baseline["features"]["categorical"][feat]
                expected_probs_dict = base["probabilities"]
                
                counts = df[feat].value_counts(normalize=True).to_dict()
                
                categories = list(set(expected_probs_dict.keys()).union(set(counts.keys())))
                
                expected_probs = [expected_probs_dict.get(c, 0.0) for c in categories]
                actual_probs = [counts.get(c, 0.0) for c in categories]
                
                psi = self.calculate_psi(expected_probs, actual_probs)
                severity = self.get_severity(psi, "categorical")
                
                results["features"].append({
                    "feature_name": feat,
                    "type": "categorical",
                    "drift_detected": severity != "NO_DRIFT",
                    "drift_score": psi,
                    "severity": severity
                })
                
        # Analyze Prediction Drift
        if "prediction" in self.baseline["features"] and "fraud_probability" in df.columns:
            base = self.baseline["features"]["prediction"]
            bins = base["bins"]
            expected_probs = base["probabilities"]
            
            counts, _ = np.histogram(df["fraud_probability"], bins=bins)
            actual_probs = counts / counts.sum()
            
            psi = self.calculate_psi(expected_probs, actual_probs)
            severity = self.get_severity(psi, "numerical")
            
            results["prediction_drift"] = {
                "drift_detected": severity != "NO_DRIFT",
                "drift_score": psi,
                "severity": severity,
                "metric_name": "Prediction Distribution Shift"
            }
            
        return results

drift_analyzer = DriftAnalyzer()
