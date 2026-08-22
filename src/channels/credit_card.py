from typing import Any, Dict
from src.channels.base import BasePaymentChannel

class CreditCardChannel(BasePaymentChannel):
    """
    Simulates a Credit Card processing channel.
    Expects card-specific fields like 'pan_last_four' and 'merchant_id'.
    """
    def validate(self, payload: Dict[str, Any]) -> bool:
        required_fields = ['transaction_id', 'pan_last_four', 'merchant_id', 'amount']
        return all(field in payload for field in required_fields)
        
    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "step": 1, 
            "type": "PAYMENT",
            "amount": payload["amount"],
            "oldbalanceOrg": payload.get("available_credit", 0.0), 
            "oldbalanceDest": 0.0, # Merchants typically don't have a visible pre-balance
            "channel": "CREDIT_CARD"
        }
