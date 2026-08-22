import yaml
import os

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/risk_decision_policy.yaml'))

class ContextAwareDecisionEngine:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        with open(CONFIG_PATH, 'r') as file:
            self.config = yaml.safe_load(file)
            self.policy_version = self.config.get('policy_version', 'v1.0')
            self.thresholds = self.config['thresholds']
            self.rules = self.config['rules']

    def assess_risk(self, fraud_probability: float, amount: float, behavioral_signal: float, history_status: str) -> dict:
        """
        Maps a continuous fraud probability and contextual signals to a risk decision policy.
        """
        decision_reasons = []
        
        # Determine Decision Confidence based on history
        if history_status == "SUFFICIENT":
            decision_confidence = "HIGH_CONFIDENCE"
        elif history_status == "LIMITED":
            decision_confidence = "MEDIUM_CONFIDENCE"
        else:
            decision_confidence = "LIMITED_CONTEXT"
            
        ml_high = self.thresholds['ml_high_risk']
        ml_medium = self.thresholds['ml_medium_risk']
        high_value = self.thresholds['high_value_amount']
        behavioral_anomaly = self.thresholds['behavioral_anomaly_threshold']

        # Rule evaluation (Ordered hierarchy)
        if fraud_probability >= ml_high:
            rule_id = "R1_ML_CERTAIN_FRAUD"
            decision = "BLOCK"
            level = "HIGH"
            decision_reasons.append(f"ML probability ({fraud_probability:.2f}) exceeds high-risk threshold ({ml_high}).")
            
        elif fraud_probability >= ml_medium and behavioral_signal >= behavioral_anomaly and history_status == "SUFFICIENT":
            rule_id = "R2_BEHAVIORAL_ANOMALY"
            decision = "BLOCK"
            level = "HIGH"
            decision_reasons.append(f"ML probability ({fraud_probability:.2f}) is elevated and behavioral signal ({behavioral_signal:.2f}) indicates severe anomaly.")
            
        elif fraud_probability >= ml_medium and amount >= high_value:
            rule_id = "R3_HIGH_VALUE_UNCERTAIN"
            decision = "VERIFY"
            level = "MEDIUM"
            decision_reasons.append(f"Transaction is medium risk and amount ({amount}) exceeds high-value threshold ({high_value}).")
            
        elif fraud_probability >= ml_medium:
            rule_id = "R4_MEDIUM_RISK"
            decision = "VERIFY"
            level = "MEDIUM"
            decision_reasons.append(f"ML probability ({fraud_probability:.2f}) exceeds medium-risk threshold ({ml_medium}).")
            
        else:
            rule_id = "R5_NOMINAL"
            decision = "APPROVE"
            level = "LOW"
            decision_reasons.append("Transaction appears safe across all signals.")

        return {
            "fraud_probability": float(fraud_probability),
            "risk_level": level,
            "recommended_action": decision,
            "decision_policy": rule_id,
            "decision_confidence": decision_confidence,
            "decision_reasons": decision_reasons,
            "policy_version": self.policy_version
        }

# Global instance for use across the API
decision_engine = ContextAwareDecisionEngine()
