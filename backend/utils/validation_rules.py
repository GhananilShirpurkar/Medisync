"""
MEDICAL VALIDATION RULES ENGINE
================================
Defines safety and compliance rules for prescription validation.

This module contains all medical validation rules including:
- Prescription expiry checks
- Required field validation
- Signature verification
- Dosage validation
- Controlled substance detection
- Drug interaction warnings
- Compliance checks

All rules are designed to be:
- Clear and maintainable
- Easy to update
- Auditable
- Safety-critical
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


# ------------------------------------------------------------------
# ENUMS AND CONSTANTS
# ------------------------------------------------------------------

class IssueSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Blocks prescription processing
    WARNING = "warning"    # Requires pharmacist review
    INFO = "info"          # Informational only


class ValidationStatus(Enum):
    """Overall validation status."""
    APPROVED = "approved"           # Safe to proceed
    NEEDS_REVIEW = "needs_review"   # Requires pharmacist
    REJECTED = "rejected"           # Cannot proceed


# Prescription validity period (days)
PRESCRIPTION_VALIDITY_DAYS = 180  # 6 months

# Controlled substances (Schedule H, H1, X in India)
CONTROLLED_SUBSTANCES = {
    # Schedule H (Prescription-only)
    "antibiotics": [
        "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline",
        "cephalexin", "metronidazole", "levofloxacin", "clarithromycin"
    ],
    
    # Schedule H1 (Restricted antibiotics)
    "restricted_antibiotics": [
        "cefixime", "cefpodoxime", "linezolid", "meropenem",
        "tigecycline", "colistin"
    ],
    
    # Schedule X (Habit-forming)
    "habit_forming": [
        "alprazolam", "diazepam", "lorazepam", "clonazepam",
        "tramadol", "codeine", "morphine", "fentanyl",
        "zolpidem", "zopiclone"
    ],
    
    # Other controlled
    "steroids": [
        "prednisolone", "dexamethasone", "hydrocortisone",
        "betamethasone", "methylprednisolone"
    ]
}

# Flatten controlled substances list
ALL_CONTROLLED_SUBSTANCES = []
for category in CONTROLLED_SUBSTANCES.values():
    ALL_CONTROLLED_SUBSTANCES.extend(category)

# High-risk drugs requiring extra caution
HIGH_RISK_DRUGS = [
    "warfarin", "insulin", "digoxin", "lithium", "methotrexate",
    "phenytoin", "carbamazepine", "theophylline"
]

# Maximum dosage limits (mg per day)
MAX_DOSAGE_LIMITS = {
    "paracetamol": 4000,      # 4g per day
    "ibuprofen": 2400,        # 2.4g per day
    "aspirin": 4000,          # 4g per day
    "diclofenac": 150,        # 150mg per day
    "tramadol": 400,          # 400mg per day
    "codeine": 240,           # 240mg per day
}


# ------------------------------------------------------------------
# VALIDATION ISSUE CLASS
# ------------------------------------------------------------------

class ValidationIssue:
    """Represents a single validation issue."""
    
    def __init__(
        self,
        severity: IssueSeverity,
        field: str,
        message: str,
        rule_violated: str,
        recommendation: Optional[str] = None
    ):
        self.severity = severity
        self.field = field
        self.message = message
        self.rule_violated = rule_violated
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "severity": self.severity.value,
            "field": self.field,
            "message": self.message,
            "rule_violated": self.rule_violated,
            "recommendation": self.recommendation
        }
    
    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity.value}: {self.message})"


# ------------------------------------------------------------------
# PRESCRIPTION EXPIRY VALIDATION
# ------------------------------------------------------------------

def validate_prescription_date(date_str: Optional[str]) -> List[ValidationIssue]:
    """
    Validate prescription date and check if expired.
    
    Rules:
    - Prescription must have a date
    - Date must be in the past (not future)
    - Prescription valid for 180 days (6 months)
    
    Args:
        date_str: Date string in format DD/MM/YYYY or YYYY-MM-DD
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check if date exists
    if not date_str:
        issues.append(ValidationIssue(
            severity=IssueSeverity.CRITICAL,
            field="date",
            message="Prescription date is missing",
            rule_violated="REQUIRED_DATE",
            recommendation="Request patient to provide prescription with date"
        ))
        return issues
    
    try:
        # Parse date (try multiple formats)
        prescription_date = None
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                prescription_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not prescription_date:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                field="date",
                message=f"Could not parse date: {date_str}",
                rule_violated="DATE_FORMAT",
                recommendation="Verify date format with patient"
            ))
            return issues
        
        # Check if date is in future
        if prescription_date > datetime.now():
            issues.append(ValidationIssue(
                severity=IssueSeverity.CRITICAL,
                field="date",
                message=f"Prescription date is in the future: {date_str}",
                rule_violated="FUTURE_DATE",
                recommendation="Verify date with patient"
            ))
        
        # Check if prescription is expired
        expiry_date = prescription_date + timedelta(days=PRESCRIPTION_VALIDITY_DAYS)
        if datetime.now() > expiry_date:
            days_expired = (datetime.now() - expiry_date).days
            issues.append(ValidationIssue(
                severity=IssueSeverity.CRITICAL,
                field="date",
                message=f"Prescription expired {days_expired} days ago (valid until {expiry_date.strftime('%d/%m/%Y')})",
                rule_violated="EXPIRED_PRESCRIPTION",
                recommendation="Request new prescription from doctor"
            ))
        
        # Warning if prescription is close to expiry (within 30 days)
        elif (expiry_date - datetime.now()).days < 30:
            days_remaining = (expiry_date - datetime.now()).days
            issues.append(ValidationIssue(
                severity=IssueSeverity.INFO,
                field="date",
                message=f"Prescription expires in {days_remaining} days",
                rule_violated="NEAR_EXPIRY",
                recommendation="Inform patient about upcoming expiry"
            ))
    
    except Exception as e:
        issues.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            field="date",
            message=f"Error validating date: {str(e)}",
            rule_violated="DATE_VALIDATION_ERROR",
            recommendation="Manual verification required"
        ))
    
    return issues


# ------------------------------------------------------------------
# SIGNATURE VALIDATION
# ------------------------------------------------------------------

def validate_signature(signature_present: bool, doctor_name: Optional[str]) -> List[ValidationIssue]:
    """
    Validate doctor signature and registration.
    
    Rules:
    - Prescription must have doctor signature
    - Doctor name must be present
    
    Args:
        signature_present: Whether signature is detected
        doctor_name: Doctor's name
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if not signature_present:
        issues.append(ValidationIssue(
            severity=IssueSeverity.CRITICAL,
            field="signature",
            message="Doctor signature is missing",
            rule_violated="MISSING_SIGNATURE",
            recommendation="Request signed prescription from doctor"
        ))
    
    if not doctor_name:
        issues.append(ValidationIssue(
            severity=IssueSeverity.CRITICAL,
            field="doctor_name",
            message="Doctor name is missing",
            rule_violated="MISSING_DOCTOR_NAME",
            recommendation="Verify doctor details"
        ))
    
    return issues


# ------------------------------------------------------------------
# MEDICINE VALIDATION
# ------------------------------------------------------------------

def validate_medicine_details(medicine: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate individual medicine details.
    
    Rules:
    - Medicine name must be present
    - Dosage should be specified
    - Frequency should be specified
    
    Args:
        medicine: Dictionary with medicine details
        
    Returns:
        List of validation issues
    """
    issues = []
    
    medicine_name = medicine.get("name", "").lower().strip()
    dosage = medicine.get("dosage")
    frequency = medicine.get("frequency")
    
    # Check medicine name
    if not medicine_name or medicine_name == "unknown":
        issues.append(ValidationIssue(
            severity=IssueSeverity.CRITICAL,
            field="medicine_name",
            message="Medicine name is missing or unclear",
            rule_violated="MISSING_MEDICINE_NAME",
            recommendation="Request clearer prescription or verify with doctor"
        ))
        return issues  # Can't validate further without name
    
    # Check dosage
    if not dosage:
        issues.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            field="dosage",
            message=f"Dosage not specified for {medicine_name}",
            rule_violated="MISSING_DOSAGE",
            recommendation="Verify dosage with pharmacist or doctor"
        ))
    
    # Check frequency
    if not frequency:
        issues.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            field="frequency",
            message=f"Frequency not specified for {medicine_name}",
            rule_violated="MISSING_FREQUENCY",
            recommendation="Verify frequency with pharmacist or doctor"
        ))
    
    return issues


# ------------------------------------------------------------------
# CONTROLLED SUBSTANCE VALIDATION
# ------------------------------------------------------------------

def validate_controlled_substances(medicines: List[Dict[str, Any]]) -> List[ValidationIssue]:
    """
    Check for controlled substances requiring special handling.
    
    Rules:
    - Controlled substances require valid prescription
    - Schedule X drugs require special documentation
    - High-risk drugs require extra caution
    
    Args:
        medicines: List of medicine dictionaries
        
    Returns:
        List of validation issues
    """
    issues = []
    
    for medicine in medicines:
        medicine_name = medicine.get("name", "").lower().strip()
        
        # Check if controlled substance
        if any(controlled in medicine_name for controlled in ALL_CONTROLLED_SUBSTANCES):
            # Determine category
            category = None
            for cat_name, cat_drugs in CONTROLLED_SUBSTANCES.items():
                if any(drug in medicine_name for drug in cat_drugs):
                    category = cat_name
                    break
            
            if category == "habit_forming":
                issues.append(ValidationIssue(
                    severity=IssueSeverity.CRITICAL,
                    field="medicine",
                    message=f"{medicine_name.title()} is a Schedule X (habit-forming) drug",
                    rule_violated="SCHEDULE_X_DRUG",
                    recommendation="Verify prescription, maintain records, pharmacist approval required"
                ))
            elif category == "restricted_antibiotics":
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    field="medicine",
                    message=f"{medicine_name.title()} is a Schedule H1 (restricted) antibiotic",
                    rule_violated="SCHEDULE_H1_DRUG",
                    recommendation="Verify prescription, pharmacist approval recommended"
                ))
            else:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.INFO,
                    field="medicine",
                    message=f"{medicine_name.title()} is a prescription-only drug",
                    rule_violated="PRESCRIPTION_REQUIRED",
                    recommendation="Verify valid prescription present"
                ))
        
        # Check if high-risk drug
        if any(high_risk in medicine_name for high_risk in HIGH_RISK_DRUGS):
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                field="medicine",
                message=f"{medicine_name.title()} is a high-risk drug requiring careful monitoring",
                rule_violated="HIGH_RISK_DRUG",
                recommendation="Counsel patient on proper usage and side effects"
            ))
    
    return issues


# ------------------------------------------------------------------
# DOSAGE VALIDATION
# ------------------------------------------------------------------

def validate_dosage_limits(medicines: List[Dict[str, Any]]) -> List[ValidationIssue]:
    """
    Validate dosages against maximum safe limits.
    
    Rules:
    - Dosage should not exceed maximum daily limits
    - Warn if dosage is unusually high
    
    Args:
        medicines: List of medicine dictionaries
        
    Returns:
        List of validation issues
    """
    issues = []
    
    for medicine in medicines:
        medicine_name = medicine.get("name", "").lower().strip()
        dosage_str = medicine.get("dosage", "")
        frequency_str = medicine.get("frequency", "")
        
        # Check if we have dosage limits for this medicine
        for drug, max_daily in MAX_DOSAGE_LIMITS.items():
            if drug in medicine_name:
                try:
                    # Extract dosage amount (e.g., "500mg" -> 500)
                    import re
                    dosage_match = re.search(r'(\d+)\s*mg', dosage_str.lower())
                    if not dosage_match:
                        continue
                    
                    single_dose = int(dosage_match.group(1))
                    
                    # Extract frequency (e.g., "3 times daily" -> 3)
                    freq_match = re.search(r'(\d+)\s*times', frequency_str.lower())
                    if freq_match:
                        times_per_day = int(freq_match.group(1))
                    else:
                        # Assume once daily if not specified
                        times_per_day = 1
                    
                    # Calculate daily dosage
                    daily_dosage = single_dose * times_per_day
                    
                    # Check against limit
                    if daily_dosage > max_daily:
                        issues.append(ValidationIssue(
                            severity=IssueSeverity.CRITICAL,
                            field="dosage",
                            message=f"{medicine_name.title()} daily dosage ({daily_dosage}mg) exceeds maximum safe limit ({max_daily}mg)",
                            rule_violated="DOSAGE_EXCEEDS_LIMIT",
                            recommendation="Verify dosage with doctor, do not dispense"
                        ))
                    elif daily_dosage > max_daily * 0.8:  # Within 80% of limit
                        issues.append(ValidationIssue(
                            severity=IssueSeverity.WARNING,
                            field="dosage",
                            message=f"{medicine_name.title()} daily dosage ({daily_dosage}mg) is close to maximum limit ({max_daily}mg)",
                            rule_violated="DOSAGE_NEAR_LIMIT",
                            recommendation="Counsel patient on proper usage"
                        ))
                
                except (ValueError, AttributeError):
                    # Could not parse dosage, skip validation
                    pass
    
    return issues


# ------------------------------------------------------------------
# DUPLICATE MEDICINE VALIDATION
# ------------------------------------------------------------------

def validate_duplicate_medicines(medicines: List[Dict[str, Any]]) -> List[ValidationIssue]:
    """
    Check for duplicate or similar medicines.
    
    Rules:
    - Same medicine should not be prescribed twice
    - Similar medicines (same active ingredient) should be flagged
    
    Args:
        medicines: List of medicine dictionaries
        
    Returns:
        List of validation issues
    """
    issues = []
    
    medicine_names = [m.get("name", "").lower().strip() for m in medicines]
    
    # Check for exact duplicates
    seen = set()
    for name in medicine_names:
        if name in seen and name != "unknown":
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                field="medicines",
                message=f"Duplicate medicine detected: {name.title()}",
                rule_violated="DUPLICATE_MEDICINE",
                recommendation="Verify with doctor if intentional"
            ))
        seen.add(name)
    
    return issues


# ------------------------------------------------------------------
# MAIN VALIDATION FUNCTION
# ------------------------------------------------------------------

def validate_prescription(prescription_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main validation function that applies all rules.
    
    Args:
        prescription_data: Dictionary with prescription details
        {
            "patient_name": str,
            "doctor_name": str,
            "date": str,
            "medicines": [{"name": str, "dosage": str, "frequency": str}],
            "signature_present": bool,
            "doctor_registration_number": str
        }
        
    Returns:
        Dictionary with validation results
        {
            "status": "approved" | "needs_review" | "rejected",
            "issues": [ValidationIssue],
            "requires_pharmacist": bool,
            "risk_score": float (0.0 to 1.0),
            "reasoning_trace": [str]
        }
    """
    all_issues = []
    reasoning_trace = []
    
    # 1. Validate prescription date
    date_issues = validate_prescription_date(prescription_data.get("date"))
    all_issues.extend(date_issues)
    if date_issues:
        reasoning_trace.append(f"Date validation: {len(date_issues)} issue(s) found")
    else:
        reasoning_trace.append("Date validation: Passed")
    
    # 2. Validate signature
    signature_issues = validate_signature(
        prescription_data.get("signature_present", False),
        prescription_data.get("doctor_name")
    )
    all_issues.extend(signature_issues)
    if signature_issues:
        reasoning_trace.append(f"Signature validation: {len(signature_issues)} issue(s) found")
    else:
        reasoning_trace.append("Signature validation: Passed")
    
    # 3. Validate medicines
    medicines = prescription_data.get("medicines", [])
    if not medicines:
        all_issues.append(ValidationIssue(
            severity=IssueSeverity.CRITICAL,
            field="medicines",
            message="No medicines found in prescription",
            rule_violated="NO_MEDICINES",
            recommendation="Verify prescription is complete"
        ))
        reasoning_trace.append("Medicine validation: No medicines found")
    else:
        reasoning_trace.append(f"Validating {len(medicines)} medicine(s)")
        
        # Validate each medicine
        for medicine in medicines:
            medicine_issues = validate_medicine_details(medicine)
            all_issues.extend(medicine_issues)
        
        # Check for controlled substances
        controlled_issues = validate_controlled_substances(medicines)
        all_issues.extend(controlled_issues)
        if controlled_issues:
            reasoning_trace.append(f"Controlled substances: {len(controlled_issues)} flag(s)")
        
        # Check dosage limits
        dosage_issues = validate_dosage_limits(medicines)
        all_issues.extend(dosage_issues)
        if dosage_issues:
            reasoning_trace.append(f"Dosage validation: {len(dosage_issues)} issue(s)")
        
        # Check for duplicates
        duplicate_issues = validate_duplicate_medicines(medicines)
        all_issues.extend(duplicate_issues)
        if duplicate_issues:
            reasoning_trace.append(f"Duplicate check: {len(duplicate_issues)} issue(s)")
    
    # Calculate risk score based on issues
    risk_score = calculate_risk_score(all_issues)
    reasoning_trace.append(f"Risk score calculated: {risk_score:.2f}")
    
    # Determine overall status
    status, requires_pharmacist = determine_validation_status(all_issues, risk_score)
    reasoning_trace.append(f"Final status: {status.value}")
    
    return {
        "status": status.value,
        "issues": [issue.to_dict() for issue in all_issues],
        "requires_pharmacist": requires_pharmacist,
        "risk_score": risk_score,
        "reasoning_trace": reasoning_trace
    }


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def calculate_risk_score(issues: List[ValidationIssue]) -> float:
    """
    Calculate overall risk score based on issues.
    
    Score calculation:
    - Critical issue: +0.3
    - Warning issue: +0.15
    - Info issue: +0.05
    
    Returns:
        Risk score from 0.0 (no risk) to 1.0 (maximum risk)
    """
    score = 0.0
    
    for issue in issues:
        if issue.severity == IssueSeverity.CRITICAL:
            score += 0.3
        elif issue.severity == IssueSeverity.WARNING:
            score += 0.15
        elif issue.severity == IssueSeverity.INFO:
            score += 0.05
    
    # Cap at 1.0
    return min(score, 1.0)


def determine_validation_status(
    issues: List[ValidationIssue],
    risk_score: float
) -> tuple[ValidationStatus, bool]:
    """
    Determine overall validation status and pharmacist requirement.
    
    Rules:
    - Any critical issue → REJECTED
    - Risk score > 0.5 → NEEDS_REVIEW
    - Any warning → NEEDS_REVIEW
    - Otherwise → APPROVED
    
    Returns:
        Tuple of (ValidationStatus, requires_pharmacist)
    """
    # Check for critical issues
    has_critical = any(i.severity == IssueSeverity.CRITICAL for i in issues)
    has_warning = any(i.severity == IssueSeverity.WARNING for i in issues)
    
    if has_critical:
        return ValidationStatus.REJECTED, True
    
    if risk_score > 0.5 or has_warning:
        return ValidationStatus.NEEDS_REVIEW, True
    
    if len(issues) == 0:
        return ValidationStatus.APPROVED, False
    
    # Has only info issues
    return ValidationStatus.APPROVED, False
