from sqlalchemy.orm import Session
from database.models import FraudCase, TransactionAuditLog
import logging

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self, min_labelled_sample_size=50):
        self.min_labelled_sample_size = min_labelled_sample_size

    def analyze_performance(self, db: Session):
        """
        Calculates LIVE Precision, Recall, and FPR based on Analyst resolutions.
        True Positive = Model said Fraud, Analyst said CONFIRMED_FRAUD.
        False Positive = Model said Fraud, Analyst said FALSE_POSITIVE (or VERIFIED_LEGITIMATE).
        False Negative = Model said Legit, Analyst said CONFIRMED_FRAUD (Requires a feedback loop from outside, but for now we only know what we caught).
        
        Since we only create cases for BLOCK/VERIFY, we can only accurately calculate Precision right now.
        To calculate Recall, we need labels for APPROVE transactions that were later reported as fraud (e.g. by chargebacks).
        """
        
        resolved_cases = db.query(FraudCase).filter(FraudCase.status == "RESOLVED").all()
        
        if len(resolved_cases) < self.min_labelled_sample_size:
            return {
                "status": "INSUFFICIENT_LABELLED_DATA",
                "sample_size": len(resolved_cases),
                "min_required": self.min_labelled_sample_size,
                "metrics": None
            }
            
        true_positives = 0
        false_positives = 0
        
        for case in resolved_cases:
            if case.resolution == "CONFIRMED_FRAUD":
                true_positives += 1
            elif case.resolution in ["FALSE_POSITIVE", "VERIFIED_LEGITIMATE"]:
                false_positives += 1
                
        total_flagged = true_positives + false_positives
        
        if total_flagged == 0:
            precision = 0.0
        else:
            precision = true_positives / total_flagged
            
        return {
            "status": "SUCCESS",
            "sample_size": len(resolved_cases),
            "metrics": {
                "precision": precision,
                # Recall and FPR require knowing true negatives and false negatives (chargebacks).
                "recall": "N/A - Requires Chargeback Data",
                "false_positive_rate": "N/A - Requires Chargeback Data",
                "true_positives": true_positives,
                "false_positives": false_positives
            }
        }

performance_analyzer = PerformanceAnalyzer()
