import collections

class BehavioralEngine:
    def __init__(self):
        # In-memory history stores.
        # Maps user ID (e.g. nameOrig or nameDest) to a list of historical transaction amounts.
        self.sender_history = collections.defaultdict(list)
        self.recipient_history = collections.defaultdict(list)
        
    def assess_transaction(self, transaction_data: dict) -> dict:
        """
        Calculates behavioral features for the CURRENT transaction based on PAST history.
        Does NOT modify history to prevent leakage.
        """
        sender = transaction_data.get("nameOrig")
        recipient = transaction_data.get("nameDest")
        amount = transaction_data.get("amount", 0.0)
        
        features = {
            "behavioral_history_status": "NONE",
            "sender_transaction_count_recent": 0,
            "recipient_transaction_count_recent": 0,
            "amount_deviation_score": 0.0,
            "is_new_recipient": True,
            "behavioral_risk_signal": 0.0
        }
        
        has_sender_history = False
        has_recipient_history = False

        if sender and sender in self.sender_history:
            history = self.sender_history[sender]
            if len(history) > 0:
                has_sender_history = True
                features["sender_transaction_count_recent"] = len(history)
                
                # Calculate simple deviation heuristic
                avg_amount = sum(history) / len(history)
                deviation = (amount - avg_amount) / (avg_amount + 1.0)
                features["amount_deviation_score"] = float(deviation)
                
                # If transaction is massive compared to average, boost signal
                if deviation > 5.0:
                    features["behavioral_risk_signal"] += 0.3
                if deviation > 10.0:
                    features["behavioral_risk_signal"] += 0.2
        
        if recipient and recipient in self.recipient_history:
            history = self.recipient_history[recipient]
            if len(history) > 0:
                has_recipient_history = True
                features["recipient_transaction_count_recent"] = len(history)
                features["is_new_recipient"] = False
        
        if features["is_new_recipient"]:
            # New recipient adds minor risk heuristic
            features["behavioral_risk_signal"] += 0.1
                
        if has_sender_history and has_recipient_history:
            features["behavioral_history_status"] = "SUFFICIENT"
        elif has_sender_history or has_recipient_history:
            features["behavioral_history_status"] = "LIMITED"
            
        # Cap signal at 1.0
        features["behavioral_risk_signal"] = min(features["behavioral_risk_signal"], 1.0)
            
        return features
        
    def record_transaction(self, transaction_data: dict):
        """
        Stores the current transaction in history for FUTURE analysis.
        This must be called AFTER the ML prediction to prevent data leakage.
        """
        sender = transaction_data.get("nameOrig")
        recipient = transaction_data.get("nameDest")
        amount = transaction_data.get("amount", 0.0)
        
        if sender:
            self.sender_history[sender].append(amount)
            if len(self.sender_history[sender]) > 50:
                self.sender_history[sender].pop(0)
                
        if recipient:
            self.recipient_history[recipient].append(amount)
            if len(self.recipient_history[recipient]) > 50:
                self.recipient_history[recipient].pop(0)

behavioral_engine = BehavioralEngine()
