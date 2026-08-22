import yaml
import os

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/risk_thresholds.yaml'))

class DecisionEngine:
    def __init__(self):
        self._load_config()

    def _load_config(self):
        with open(CONFIG_PATH, 'r') as file:
            config = yaml.safe_load(file)
            self.high_threshold = config['thresholds']['high_risk_threshold']
            self.medium_threshold = config['thresholds']['medium_risk_threshold']
            self.policies = config['policies']

    def assess_risk(self, fraud_probability: float) -> dict:
        """
        Maps a continuous fraud probability [0.0 - 1.0] to a risk decision policy.
        """
        if fraud_probability >= self.high_threshold:
            policy = self.policies['high_risk']
            policy_id = "high_risk_threshold_exceeded"
        elif fraud_probability >= self.medium_threshold:
            policy = self.policies['medium_risk']
            policy_id = "medium_risk_threshold_exceeded"
        else:
            policy = self.policies['low_risk']
            policy_id = "low_risk_cleared"

        return {
            "fraud_probability": float(fraud_probability),
            "risk_level": policy['level'],
            "recommended_action": policy['action'],
            "decision_policy": policy_id
        }

# Global instance for use across the API
decision_engine = DecisionEngine()
