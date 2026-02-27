import re
from typing import Optional, Dict, Tuple
from datetime import datetime
from src.database import Database
from src.models import Patient

class IdentityAgent:
    """
    Agent responsible for resolving patient identity via phone number.
    
    Capabilities:
    1. Extract phone numbers from text
    2. Normalize phone numbers
    3. Retrieve or create patient records
    """
    
    def __init__(self):
        self.db = Database()
        # Regex for common phone formats (focus on Indian context +91)
        # Matches: +91 9876543210, 9876543210, 98765-43210
        self.phone_pattern = r"(?:\+91[\-\s]?)?[6-9]\d{9}|[6-9]\d{4}[\-\s]\d{5}"

    def extract_phone_number(self, text: str) -> Optional[str]:
        """Extract first valid phone number from text."""
        match = re.search(self.phone_pattern, text)
        if match:
            return self._normalize_phone(match.group(0))
        return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize to +91XXXXXXXXXX format."""
        # Remove non-digits
        digits = re.sub(r"\D", "", phone)
        
        # Handle country code
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        
        # Fallback (should be covered by regex, but for safety)
        return f"+{digits}"

    def resolve_identity(self, phone: str, name: Optional[str] = None) -> Dict:
        """
        Get or create patient by phone number.
        Returns patient dictionary with PID.
        """
        return self.db.resolve_patient(phone, name)

    def is_phone_number_query(self, text: str) -> bool:
        """Check if the text implies providing a phone number."""
        return bool(self.extract_phone_number(text))

    def link_telegram(self, pid: str, telegram_id: str) -> bool:
        """Link a Telegram ID to a Patient ID."""
        return self.db.update_patient_telegram(pid, telegram_id)

    def get_pid_by_telegram(self, telegram_id: str) -> Optional[str]:
        """Get PID associated with a Telegram ID."""
        return self.db.get_patient_by_telegram(telegram_id)
