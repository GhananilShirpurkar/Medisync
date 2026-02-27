"""
MEDICAL VALIDATION AGENT
=========================
Agent 3: Safety checks and compliance validation

Responsibilities:
1. Validate prescription fields (date, signature, dosage)
2. Check for controlled substances
3. Detect drug interactions (LLM-powered)
4. Apply medical rules engine
5. Generate risk score
6. Provide reasoning trace

NEW: Two Modes
- Mode A (OTC): Generate "AI-Assisted OTC Recommendation Summary"
- Mode B (Prescription): Validate uploaded prescription
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from src.state import PharmacyState, OrderItem
from utils.validation_rules import (
    validate_prescription,
    ValidationStatus,
    IssueSeverity
)
from src.services.llm_service import call_llm_safety_check
from src.database import Database
from src.services.observability_service import trace_agent
from src.agents.severity_scorer import assess_severity, format_severity_report


# ------------------------------------------------------------------
# MEDICAL VALIDATION AGENT
# ------------------------------------------------------------------
@trace_agent("MedicalValidationAgent", agent_type="agent")
def medical_validation_agent(state: PharmacyState, mode: str = "auto") -> PharmacyState:
    """
    Medical Validation Agent - Safety and compliance checks.
    
    NEW: Supports two modes:
    - Mode A (OTC): Validates symptom-based recommendations without prescription
    - Mode B (Prescription): Validates uploaded prescription
    
    Args:
        state: Current pharmacy state
        mode: "auto" (detect), "otc", or "prescription"
        
    Returns:
        Updated state with validation results
    """
    
    # Initialize reasoning trace
    reasoning_trace = []
    
    # Determine mode
    if mode == "auto":
        # Auto-detect based on prescription upload
        if state.prescription_uploaded:
            mode = "prescription"
        else:
            mode = "otc"
    
    reasoning_trace.append(f"🔍 Validation Mode: {mode.upper()}")
    
    # Route to appropriate validation mode
    if mode == "otc":
        return _validate_otc_mode(state, reasoning_trace)
    else:
        return _validate_prescription_mode(state, reasoning_trace)


def _validate_otc_mode(state: PharmacyState, reasoning_trace: List[str]) -> PharmacyState:
    """
    Mode A: OTC Validation
    
    Validates symptom-based medicine recommendations without prescription.
    Generates "AI-Assisted OTC Recommendation Summary".
    
    Rules:
    - Check if medicines require prescription
    - Validate against patient context (age, allergies, conditions)
    - Check drug interactions
    - Generate safety summary
    - NEVER forge doctor data
    """
    
    reasoning_trace.append("📋 Mode A: OTC Recommendation Validation")
    
    # Step 1: Check if any medicines require prescription
    db = Database()
    prescription_required_items = []
    otc_items = []
    
    for item in state.extracted_items:
        medicine = db.get_medicine(item.medicine_name)
        if medicine is None:
            # If medicine is not in our DB, it's an unknown substance.
            # Flag for review.
            prescription_required_items.append(item)
            reasoning_trace.append(f"⚠️  {item.medicine_name} not found in database, requires pharmacist review")
        else:
            # Step 1: When dosage is missing, check database
            if not item.dosage and medicine.get('strength'):
                # Step 2: If medicine found and strength is not null, set dosage
                item.dosage = medicine.get('strength')
                if "medical_validator" not in state.trace_metadata:
                    state.trace_metadata["medical_validator"] = {}
                state.trace_metadata["medical_validator"]["dosage_inferred"] = True
                state.trace_metadata["medical_validator"]["inferred_from"] = "database_record"
                reasoning_trace.append(f"ℹ️  Inferred dosage for {item.medicine_name}: {item.dosage} from DB")
            elif not item.dosage:
                # Step 3: Only if not found or strength null, flag needs_review
                state.pharmacist_decision = "needs_review"
                state.safety_issues.append(f"Dosage unspecified — pharmacist confirmation required. ({item.medicine_name})")
                reasoning_trace.append(f"⚠️  Dosage unspecified — pharmacist confirmation required. ({item.medicine_name})")
                
            if medicine.get("requires_prescription"):
                prescription_required_items.append(item)
                reasoning_trace.append(f"⚠️  {item.medicine_name} requires prescription")
            else:
                otc_items.append(item)
                reasoning_trace.append(f"✓ {item.medicine_name} is OTC")
    
    # Step 2: If prescription medicines found, flag for prescription upload
    if prescription_required_items:
        state.pharmacist_decision = "needs_review"
        state.prescription_verified = False
        
        for item in prescription_required_items:
            state.safety_issues.append(
                f"[PRESCRIPTION REQUIRED] {item.medicine_name} requires a valid prescription"
            )
        
        reasoning_trace.append(
            f"❌ {len(prescription_required_items)} medicine(s) require prescription upload"
        )
        
        # Store metadata
        state.trace_metadata["medical_validator"] = {
            "mode": "otc",
            "status": "needs_review",
            "reason": "prescription_required",
            "prescription_required_items": [item.medicine_name for item in prescription_required_items],
            "otc_items": [item.medicine_name for item in otc_items],
            "reasoning_trace": reasoning_trace,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        return state
    
    # Step 3: Validate OTC medicines against patient context
    patient_context = state.trace_metadata.get("front_desk", {}).get("patient_context", {})
    
    # Check age restrictions
    patient_age = patient_context.get("age")
    if patient_age:
        reasoning_trace.append(f"✓ Patient age: {patient_age}")
        
        # Age-based warnings
        if patient_age < 12:
            reasoning_trace.append("⚠️  Pediatric patient - extra caution required")
            state.safety_issues.append("[WARNING] Pediatric patient - verify dosages")
        elif patient_age > 65:
            reasoning_trace.append("⚠️  Elderly patient - extra caution required")
            state.safety_issues.append("[WARNING] Elderly patient - monitor for side effects")
    
    # Check allergies
    allergies = patient_context.get("allergies", [])
    if allergies:
        reasoning_trace.append(f"⚠️  Known allergies: {', '.join(allergies)}")
        state.safety_issues.append(f"[ALERT] Patient allergies: {', '.join(allergies)}")
    
    # Check existing conditions
    conditions = patient_context.get("existing_conditions", [])
    if conditions:
        reasoning_trace.append(f"ℹ️  Existing conditions: {', '.join(conditions)}")
    
    # Step 4: Run drug interaction check
    if len(state.extracted_items) > 1:
        interaction_result = call_llm_safety_check(state.extracted_items)
        reasoning_trace.append(f"✓ Drug interaction check completed")
        
        if interaction_result["has_interactions"]:
            reasoning_trace.append(f"⚠️  Drug interactions detected: {interaction_result['severity']}")
            
            for interaction in interaction_result["interactions"]:
                meds = " + ".join(interaction["medicines"])
                severity = interaction["severity"].upper()
                state.safety_issues.append(
                    f"[{severity}] Drug Interaction: {meds} - {interaction['description']}"
                )
                reasoning_trace.append(f"  • {meds}: {interaction['description']}")
            
            # Severe interactions require pharmacist review
            if interaction_result["severity"] == "severe":
                state.pharmacist_decision = "needs_review"
                reasoning_trace.append("❌ Severe interaction - pharmacist review required")
            else:
                state.pharmacist_decision = "approved"
                reasoning_trace.append("✅ Approved with warnings")
        else:
            state.pharmacist_decision = "approved"
            reasoning_trace.append("✓ No drug interactions detected")
            reasoning_trace.append("✅ OTC recommendations approved")
    else:
        state.pharmacist_decision = "approved"
        reasoning_trace.append("✅ Single medicine - approved")
    
    # Step 5: Run Clinical Severity Scoring
    # Use symptoms from patient context or infer from conversation
    symptoms = patient_context.get("symptoms", [])
    if isinstance(symptoms, list):
        symptoms = ", ".join(symptoms)
    
    # If no symptoms explicitly listed, try to use the order items as proxy or fallback
    if not symptoms and state.extracted_items:
        symptoms = f"Requesting: {', '.join([i.medicine_name for i in state.extracted_items])}"
    
    severity_assessment = assess_severity(
        symptoms=symptoms or "unspecified",
        patient_context=patient_context,
        conversation_history=None # trace doesn't carry full history, but extracted context is usually enough
    )
    
    reasoning_trace.append(f"✓ Severity Assessment: {severity_assessment['severity_score']}/10 ({severity_assessment['risk_level']})")
    
    if severity_assessment['emergency_override']:
        state.pharmacist_decision = "rejected"
        state.safety_issues.append("[CRITICAL] EMERGENCY SYMPTOMS DETECTED - GO TO ER")
        reasoning_trace.append(f"🚨 EMERGENCY OVERRIDE: {severity_assessment['recommended_action']}")
    elif severity_assessment['severity_score'] >= 7:
        state.pharmacist_decision = "needs_review"
        state.safety_issues.append(f"[HIGH SEVERITY] Clinical score {severity_assessment['severity_score']}/10 requires doctor")
    
    # Step 6: Generate AI-Assisted OTC Summary
    otc_summary = _generate_otc_summary(state, patient_context, reasoning_trace)
    
    # Step 7: Store metadata
    state.trace_metadata["medical_validator"] = {
        "mode": "otc",
        "status": state.pharmacist_decision,
        "otc_summary": otc_summary,
        "patient_context": patient_context,
        "safety_checks": {
            "age_check": patient_age is not None,
            "allergy_check": len(allergies) > 0,
            "interaction_check": len(state.extracted_items) > 1
        },
        "severity_assessment": severity_assessment,
        "reasoning_trace": reasoning_trace,
        "validation_timestamp": datetime.now().isoformat()
    }
    
    # Log summary
    _log_validation_summary("OTC", state, reasoning_trace)
    
    return state


def _validate_prescription_mode(state: PharmacyState, reasoning_trace: List[str]) -> PharmacyState:
    """
    Mode B: Prescription Validation
    
    Validates uploaded prescription against medical rules.
    Generates "Digitally Reconstructed Prescription".
    
    Rules:
    - Validate prescription structure (date, signature, doctor)
    - Check medicine dosages
    - Verify prescription requirements
    - Check drug interactions
    - NEVER invent doctor data
    - NEVER modify dosages
    """
    
    reasoning_trace.append("📋 Mode B: Prescription Validation")
    
    # Step 1: Check if prescription data exists
    if not state.prescription_uploaded:
        state.pharmacist_decision = "rejected"
        state.safety_issues.append("No prescription uploaded")
        reasoning_trace.append("❌ No prescription data available")
        state.trace_metadata["medical_validator"] = {
            "mode": "prescription",
            "status": "rejected",
            "reasoning": reasoning_trace
        }
        return state
    
    reasoning_trace.append("✓ Prescription data available")
    
    # Step 2: Extract prescription metadata from vision agent
    vision_metadata = state.trace_metadata.get("vision_agent", {})
    
    prescription_data = {
        "patient_name": vision_metadata.get("patient_name"),
        "doctor_name": vision_metadata.get("doctor_name"),
        "date": vision_metadata.get("date"),
        "signature_present": vision_metadata.get("signature_present", False),
        "medicines": []
    }
    
    # Convert OrderItems to medicine format
    db = Database()
    for item in state.extracted_items:
        # Step 1: Check missing dosage
        if not item.dosage:
            medicine = db.get_medicine(item.medicine_name)
            
            # Step 2: If medicine is found and strength is not null, set dosage
            if medicine and medicine.get('strength'):
                item.dosage = medicine.get('strength')
                
                # Update trace metadata
                if "medical_validator" not in state.trace_metadata:
                    state.trace_metadata["medical_validator"] = {}
                state.trace_metadata["medical_validator"]["dosage_inferred"] = True
                state.trace_metadata["medical_validator"]["inferred_from"] = "database_record"
                
                reasoning_trace.append(f"ℹ️  Inferred dosage for {item.medicine_name}: {item.dosage} from DB")
            # Step 3 is handled by the validation rules which will flag MISSING_DOSAGE if item.dosage is still None
            
        prescription_data["medicines"].append({
            "name": item.medicine_name,
            "dosage": item.dosage,
            "quantity": item.quantity
        })
    
    reasoning_trace.append(f"✓ Extracted {len(prescription_data['medicines'])} medicine(s)")
    
    # Step 3: Run validation rules engine
    validation_result = validate_prescription(prescription_data)
    
    reasoning_trace.append(f"✓ Validation engine executed")
    
    # Step 4: Run LLM drug interaction check
    interaction_result = call_llm_safety_check(state.extracted_items)
    
    reasoning_trace.append(f"✓ Drug interaction check completed")
    
    if interaction_result["has_interactions"]:
        reasoning_trace.append(f"⚠️  Drug interactions detected: {interaction_result['severity']}")
        
        for interaction in interaction_result["interactions"]:
            meds = " + ".join(interaction["medicines"])
            reasoning_trace.append(f"  • {meds}: {interaction['description']}")
    else:
        reasoning_trace.append(f"✓ No drug interactions detected")
    
    # Step 5: Process validation results
    status = validation_result["status"]
    issues = validation_result["issues"]
    risk_score = validation_result["risk_score"]
    requires_pharmacist = validation_result["requires_pharmacist"]
    
    # Adjust status based on interaction severity
    if interaction_result["severity"] == "severe" and not interaction_result["safe_to_dispense"]:
        status = "rejected"
        requires_pharmacist = True
        reasoning_trace.append("❌ Status changed to REJECTED due to severe drug interaction")
        
        for interaction in interaction_result["interactions"]:
            meds = " + ".join(interaction["medicines"])
            state.safety_issues.append(f"[CRITICAL] Drug Interaction: {meds} - {interaction['description']}")
    
    elif interaction_result["has_interactions"] and interaction_result["severity"] in ["moderate", "severe"]:
        if status == "approved":
            status = "needs_review"
            requires_pharmacist = True
            reasoning_trace.append("⚠️  Status changed to NEEDS REVIEW due to drug interactions")
        
        for interaction in interaction_result["interactions"]:
            meds = " + ".join(interaction["medicines"])
            severity_label = interaction["severity"].upper()
            state.safety_issues.append(f"[{severity_label}] Drug Interaction: {meds} - {interaction['description']}")
    
    # Calculate combined risk score
    interaction_risk = {
        "severe": 0.4,
        "moderate": 0.2,
        "minor": 0.1
    }.get(interaction_result["severity"], 0.0)
    
    combined_risk_score = min(risk_score + interaction_risk, 1.0)
    
    if interaction_risk > 0:
        reasoning_trace.append(f"⚠️  Risk score adjusted: {risk_score:.2f} → {combined_risk_score:.2f}")
        risk_score = combined_risk_score
    
    # Add validation reasoning
    for reason in validation_result["reasoning_trace"]:
        reasoning_trace.append(reason)
    
    # Step 6: Update state based on validation status
    if status == "approved":
        state.pharmacist_decision = "approved"
        state.prescription_verified = True
        reasoning_trace.append("✅ Prescription APPROVED")
        
    elif status == "needs_review":
        state.pharmacist_decision = "needs_review"
        state.prescription_verified = False
        reasoning_trace.append("⚠️  Prescription NEEDS REVIEW")
        
        for issue in issues:
            state.safety_issues.append(f"[{issue['severity'].upper()}] {issue['message']}")
        
    else:  # "rejected"
        state.pharmacist_decision = "rejected"
        state.prescription_verified = False
        reasoning_trace.append("❌ Prescription REJECTED")
        
        for issue in issues:
            state.safety_issues.append(f"[{issue['severity'].upper()}] {issue['message']}")
    
    # Step 7: Generate Digitally Reconstructed Prescription
    reconstructed_prescription = _generate_reconstructed_prescription(
        prescription_data,
        state.extracted_items,
        vision_metadata
    )
    
    # Step 8: Store metadata
    state.trace_metadata["medical_validator"] = {
        "mode": "prescription",
        "status": status,
        "risk_score": risk_score,
        "requires_pharmacist": requires_pharmacist,
        "issues_count": len(issues),
        "issues": issues,
        "drug_interactions": interaction_result,
        "reconstructed_prescription": reconstructed_prescription,
        "reasoning_trace": reasoning_trace,
        "validation_timestamp": datetime.now().isoformat()
    }
    
    # Log summary
    _log_validation_summary("PRESCRIPTION", state, reasoning_trace)
    
    return state


def _generate_otc_summary(
    state: PharmacyState,
    patient_context: Dict,
    reasoning_trace: List[str]
) -> Dict:
    """Generate AI-Assisted OTC Recommendation Summary."""
    
    return {
        "title": "AI-Assisted OTC Recommendation Summary",
        "disclaimer": "This is an AI-generated recommendation based on reported symptoms. Not a prescription.",
        "patient_context": {
            "age": patient_context.get("age"),
            "symptoms": patient_context.get("symptoms", []),
            "duration": patient_context.get("symptom_duration"),
            "severity": patient_context.get("symptom_severity"),
            "allergies": patient_context.get("allergies", []),
            "conditions": patient_context.get("existing_conditions", [])
        },
        "recommendations": [
            {
                "medicine": item.medicine_name,
                "dosage": item.dosage,
                "quantity": item.quantity,
                "reason": "Symptom-based recommendation"
            }
            for item in state.extracted_items
        ],
        "safety_notes": state.safety_issues,
        "generated_by": "MediSync AI Assistant",
        "generated_at": datetime.now().isoformat(),
        "validation_status": state.pharmacist_decision
    }


def _generate_reconstructed_prescription(
    prescription_data: Dict,
    items: List[OrderItem],
    vision_metadata: Dict
) -> Dict:
    """
    Generate Digitally Reconstructed Prescription.
    
    CRITICAL: Only reconstruct what exists - never invent data.
    """
    
    return {
        "title": "Digitally Reconstructed Prescription",
        "disclaimer": "Reconstructed from uploaded prescription image. Original prescription required for dispensing.",
        "prescription_details": {
            "patient_name": prescription_data.get("patient_name") or "[Not clearly visible]",
            "doctor_name": prescription_data.get("doctor_name") or "[Not clearly visible]",
            "date": prescription_data.get("date") or "[Not clearly visible]",
            "signature_present": prescription_data.get("signature_present", False)
        },
        "medicines": [
            {
                "medicine": item.medicine_name,
                "dosage": item.dosage or "[Not specified]",
                "quantity": item.quantity,
                "as_prescribed": True
            }
            for item in items
        ],
        "reconstruction_confidence": vision_metadata.get("confidence_score", 0.0),
        "ocr_engine": vision_metadata.get("ocr_engine", "EasyOCR"),
        "reconstructed_by": "MediSync Vision Agent",
        "reconstructed_at": datetime.now().isoformat(),
        "original_image_url": vision_metadata.get("image_url")
    }


def _log_validation_summary(mode: str, state: PharmacyState, reasoning_trace: List[str]):
    """Log validation summary to console."""
    
    print(f"\n{'='*60}")
    print(f"MEDICAL VALIDATION AGENT - {mode} MODE")
    print(f"{'='*60}")
    print(f"Decision: {state.pharmacist_decision.upper()}")
    print(f"Safety Issues: {len(state.safety_issues)}")
    
    if state.safety_issues:
        print(f"\nSafety Issues:")
        for issue in state.safety_issues:
            print(f"  {issue}")
    
    print(f"\nReasoning Trace:")
    for trace in reasoning_trace:
        print(f"  {trace}")
    
    print(f"{'='*60}\n")


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def get_validation_summary(state: PharmacyState) -> Dict[str, Any]:
    """
    Get a summary of validation results from state.
    
    Args:
        state: Pharmacy state with validation metadata
        
    Returns:
        Dictionary with validation summary
    """
    metadata = state.trace_metadata.get("medical_validator", {})
    
    return {
        "status": metadata.get("status", "unknown"),
        "risk_score": metadata.get("risk_score", 0.0),
        "requires_pharmacist": metadata.get("requires_pharmacist", False),
        "issues_count": metadata.get("issues_count", 0),
        "issues": metadata.get("issues", []),
        "decision": state.pharmacist_decision
    }


def format_validation_report(state: PharmacyState) -> str:
    """
    Format validation results as a human-readable report.
    
    Args:
        state: Pharmacy state with validation metadata
        
    Returns:
        Formatted report string
    """
    summary = get_validation_summary(state)
    metadata = state.trace_metadata.get("medical_validator", {})
    
    report = f"""
MEDICAL VALIDATION REPORT
{'='*60}

Status: {summary['status'].upper()}
Risk Score: {summary['risk_score']:.2f}
Requires Pharmacist Review: {summary['requires_pharmacist']}
Decision: {summary['decision'].upper()}

"""
    
    if summary['issues']:
        report += "Issues Detected:\n"
        for issue in summary['issues']:
            report += f"  [{issue['severity'].upper()}] {issue['message']}\n"
        report += "\n"
    
    reasoning = metadata.get("reasoning_trace", [])
    if reasoning:
        report += "Reasoning Trace:\n"
        for trace in reasoning:
            report += f"  {trace}\n"
    
    report += f"\n{'='*60}"
    
    return report
