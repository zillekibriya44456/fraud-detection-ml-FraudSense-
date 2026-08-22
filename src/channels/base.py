from typing import Any, Dict
from abc import ABC, abstractmethod

class BasePaymentChannel(ABC):
    """
    Abstract base class for all payment channels.
    This simulates an architecture that can process diverse transaction
    formats (UPI, Credit Card, ACH) before passing them to the generic
    machine learning pipeline.
    """
    @abstractmethod
    def validate(self, payload: Dict[str, Any]) -> bool:
        """Validates channel-specific required fields."""
        pass
        
    @abstractmethod
    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the channel-specific payload into the generic format 
        required by the ML model.
        """
        pass
