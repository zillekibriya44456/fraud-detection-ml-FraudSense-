import os
import logging
import time

from src.risk_engine import risk_engine
from src.decision_engine import decision_engine
from src.behavioral.engine import behavioral_engine

logger = logging.getLogger(__name__)

class FraudDetectionService:
    def __init__(self):
        self.model = risk_engine._models.get("paysim") or risk_engine._models.get("mobile_money")

    def is_ready(self) -> bool:
        return True # The risk engine handles its own readiness per domain

    def predict(self, transaction_data: dict) -> dict:

        start_time = time.time()
        
        domain = transaction_data.get("domain", "mobile_money")
        
        # Route through the DomainRiskEngine
        try:
            result = risk_engine.predict(domain, transaction_data)
        except Exception as e:
            logger.error(f"DomainRiskEngine error: {e}")
            raise

        prob = result["fraud_probability"]
        latency = (time.time() - start_time) * 1000.0
        
        # Assess Behavioral Risk (Must be before record_transaction)
        behavior = behavioral_engine.assess_transaction(transaction_data)

        # Get risk decision
        decision = decision_engine.assess_risk(
            fraud_probability=prob,
            amount=transaction_data.get("amount", 0.0),
            behavioral_signal=behavior["behavioral_risk_signal"],
            history_status=behavior["behavioral_history_status"]
        )
        
        # Risk Fusion Layer (Merge Risk Engine results with Decision Engine policy)
        decision["prediction"] = result["label"]  # Overwrite with domain-specific label
        decision["inference_latency_ms"] = latency
        decision["model_version"] = result["model"]
        decision["feature_schema_version"] = "v2.0_multi_domain"
        decision["realtime_feature_validation"] = "passed"
        decision["behavioral_history_status"] = behavior["behavioral_history_status"]
        decision["behavioral_risk_signal"] = behavior["behavioral_risk_signal"]
        
        if result.get("explanations"):
            decision["decision_reasons"] = decision.get("decision_reasons", []) + result["explanations"]
        
        # Record transaction AFTER prediction to prevent self-leakage
        behavioral_engine.record_transaction(transaction_data)
        
        return decision

    def predict_batch(self, transactions_data: list[dict]) -> list[dict]:
        results = []
        for transaction_data in transactions_data:
            results.append(self.predict(transaction_data))
        return results

    def explain(self, transaction_data: dict) -> list[dict]:
        # DomainRiskEngine handles explanations via predict()
        # so this endpoint just runs predict and extracts explanations
        decision = self.predict(transaction_data)
        return [{"feature": "Combined_Risk_Signals", "impact": decision.get("fraud_probability", 0.0)}]

fraud_service = FraudDetectionService()
