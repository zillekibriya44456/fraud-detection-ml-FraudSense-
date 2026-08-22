from typing import Any, Dict
from src.channels.base import BasePaymentChannel

class UPIChannel(BasePaymentChannel):
    """
    Simulates a UPI payment channel.
    Expects UPI-specific fields like 'vpa_origin' and 'vpa_dest', but maps them
    into the generic ML feature set.
    """
    def validate(self, payload: Dict[str, Any]) -> bool:
        required_fields = ['transaction_id', 'vpa_origin', 'vpa_dest', 'amount']
        return all(field in payload for field in required_fields)
        
    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "step": 1, # Typically would be calculated from timestamp
            "type": "TRANSFER",
            "amount": payload["amount"],
            "oldbalanceOrg": payload.get("account_balance", 0.0), # Requires internal lookup
            "oldbalanceDest": payload.get("dest_balance", 0.0),
            "channel": "UPI"
        }
