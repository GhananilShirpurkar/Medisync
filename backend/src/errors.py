"""
ERROR HIERARCHY
===============
Typed error classes for proper error handling and observability.

Error Classification:
- DomainError: Business logic violations
- ValidationError: Business rule violations
- InfrastructureError: System/external service failures
- PolicyViolation: Compliance/safety violations
"""

from typing import Optional, Dict, Any


# ------------------------------------------------------------------
# BASE ERROR CLASSES
# ------------------------------------------------------------------

class DomainError(Exception):
    """
    Base class for business logic errors.
    
    These are errors that occur within the domain logic and are
    typically recoverable or expected in normal operation.
    """
    
    severity: str = "warning"
    recoverable: bool = False
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "severity": self.severity,
            "recoverable": self.recoverable,
            "message": self.message,
            "details": self.details
        }


class InfrastructureError(Exception):
    """
    Base class for infrastructure/system errors.
    
    These are errors related to external systems, databases, APIs, etc.
    Usually recoverable with retry logic.
    """
    
    severity: str = "error"
    recoverable: bool = True
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.retry_after = retry_after  # Seconds to wait before retry
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "severity": self.severity,
            "recoverable": self.recoverable,
            "message": self.message,
            "retry_after": self.retry_after,
            "details": self.details
        }


# ------------------------------------------------------------------
# DOMAIN ERRORS (Business Logic)
# ------------------------------------------------------------------

class ValidationError(DomainError):
    """
    Business rule violation.
    
    Examples:
    - Low confidence OCR result
    - Missing required prescription fields
    - Invalid dosage format
    """
    
    severity = "warning"
    recoverable = False


class PolicyViolation(DomainError):
    """
    Compliance or safety policy violation.
    
    Examples:
    - Controlled substance without prescription
    - Expired prescription
    - Drug interaction detected
    """
    
    severity = "critical"
    recoverable = False


class InventoryError(DomainError):
    """
    Inventory-related business errors.
    
    Examples:
    - Medicine out of stock
    - Insufficient quantity
    - Medicine not found in catalog
    """
    
    severity = "warning"
    recoverable = True  # Can suggest alternatives


class FulfillmentError(DomainError):
    """
    Order fulfillment errors.
    
    Examples:
    - Order creation failed
    - Payment processing failed
    - Delivery address invalid
    """
    
    severity = "error"
    recoverable = True  # Can retry or modify order


# ------------------------------------------------------------------
# INFRASTRUCTURE ERRORS (System/External)
# ------------------------------------------------------------------

class DatabaseError(InfrastructureError):
    """
    Database connection or query errors.
    
    Examples:
    - Connection timeout
    - Query execution failed
    - Transaction rollback
    """
    
    severity = "error"
    recoverable = True


class OCRError(InfrastructureError):
    """
    OCR service errors.
    
    Examples:
    - OCR engine unavailable
    - Image processing failed
    - Low confidence extraction
    """
    
    severity = "warning"
    recoverable = True


class LLMError(InfrastructureError):
    """
    LLM service errors.
    
    Examples:
    - API rate limit exceeded
    - API key invalid
    - Service unavailable
    """
    
    severity = "warning"
    recoverable = True


class NotificationError(InfrastructureError):
    """
    Notification service errors.
    
    Examples:
    - Telegram API unavailable
    - Invalid chat ID
    - Message send failed
    """
    
    severity = "warning"
    recoverable = True  # Notifications are non-critical


# ------------------------------------------------------------------
# SPECIFIC ERROR TYPES
# ------------------------------------------------------------------

class PrescriptionExpiredError(PolicyViolation):
    """Prescription has expired."""
    
    def __init__(self, expiry_date: str):
        super().__init__(
            message=f"Prescription expired on {expiry_date}",
            details={"expiry_date": expiry_date}
        )


class ControlledSubstanceError(PolicyViolation):
    """Controlled substance requires prescription."""
    
    def __init__(self, medicine_name: str, schedule: str):
        super().__init__(
            message=f"{medicine_name} is a controlled substance (Schedule {schedule})",
            details={"medicine": medicine_name, "schedule": schedule}
        )


class DrugInteractionError(PolicyViolation):
    """Dangerous drug interaction detected."""
    
    def __init__(self, drug1: str, drug2: str, severity: str):
        super().__init__(
            message=f"Drug interaction detected: {drug1} + {drug2} ({severity})",
            details={"drug1": drug1, "drug2": drug2, "severity": severity}
        )


class LowConfidenceError(ValidationError):
    """OCR confidence below threshold."""
    
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            message=f"Low confidence: {confidence:.1%} (threshold: {threshold:.1%})",
            details={"confidence": confidence, "threshold": threshold}
        )


class MissingFieldError(ValidationError):
    """Required prescription field missing."""
    
    def __init__(self, field_name: str):
        super().__init__(
            message=f"Required field missing: {field_name}",
            details={"field": field_name}
        )


class OutOfStockError(InventoryError):
    """Medicine out of stock."""
    
    def __init__(self, medicine_name: str, requested: int, available: int = 0):
        super().__init__(
            message=f"{medicine_name} out of stock (requested: {requested}, available: {available})",
            details={
                "medicine": medicine_name,
                "requested": requested,
                "available": available
            }
        )


class TransactionError(DatabaseError):
    """Database transaction failed."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Transaction failed during {operation}: {reason}",
            retry_after=5,
            details={"operation": operation, "reason": reason}
        )


# ------------------------------------------------------------------
# ERROR HANDLER UTILITIES
# ------------------------------------------------------------------

def classify_error(error: Exception) -> Dict[str, Any]:
    """
    Classify an error and return metadata.
    
    Args:
        error: Exception to classify
        
    Returns:
        Dictionary with error classification
    """
    if isinstance(error, (DomainError, InfrastructureError)):
        return error.to_dict()
    
    # Unknown error - treat as infrastructure error
    return {
        "error_type": "UnknownError",
        "severity": "error",
        "recoverable": False,
        "message": str(error),
        "details": {"original_type": type(error).__name__}
    }


def should_retry(error: Exception) -> bool:
    """
    Determine if an error should trigger a retry.
    
    Args:
        error: Exception to check
        
    Returns:
        True if retry is appropriate
    """
    if isinstance(error, InfrastructureError):
        return error.recoverable
    
    if isinstance(error, DomainError):
        return error.recoverable
    
    return False


def get_retry_delay(error: Exception) -> int:
    """
    Get retry delay in seconds for an error.
    
    Args:
        error: Exception to check
        
    Returns:
        Seconds to wait before retry (0 if no retry)
    """
    if isinstance(error, InfrastructureError):
        return error.retry_after or 5
    
    return 0
