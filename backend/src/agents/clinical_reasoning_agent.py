"""
CLINICAL REASONING AGENT
========================
Replaces shallow semantic-similarity matching with deep clinical reasoning.
"""

import json
from typing import Dict, Any
from src.state import PharmacyState
from src.clinical_models import ClinicalResponse, ClinicalContext
from src.prompts.clinical_reasoning_v2 import CLINICAL_SYSTEM_PROMPT
from src.services.llm_service import call_llm
from src.database import Database
from src.services.contraindication_service import ContraindicationService
from src.services.interaction_service import InteractionService
from src.services.atc_service import ATCService
from src.models import Medicine

db = Database()

def parse_llm_json(response_text: str) -> Dict[str, Any]:
    """Helper to parse potentially messy JSON from LLM."""
    try:
        # Strip markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text.strip())
    except Exception as e:
        print(f"Error parsing LLM JSON: {e}")
        print(f"Raw text was: {response_text}")
        return {
            "reasoning_chain": ["Failed to parse clinical reasoning response"],
            "primary_recommendation": None,
            "information_gaps": ["Need clarification on request"]
        }


def enrich_context_from_message(state: PharmacyState) -> PharmacyState:
    """
    Simulated NER / entity extraction for the current message to update context.
    (In a full implementation, you'd use a smaller, faster LLM or SpaCy for this).
    """
    msg = state.current_message.lower()
    
    # Very rudimentary rule-based extraction for demo purposes
    if "diabetes" in msg or "diabetic" in msg:
        if "diabetes" not in state.clinical_context.comorbidities:
            state.clinical_context.comorbidities.append("diabetes")
            
    if "kidney" in msg or "ckd" in msg or "renal" in msg:
        if "kidney_disease" not in state.clinical_context.comorbidities:
            state.clinical_context.comorbidities.append("kidney_disease")
            
    if "liver" in msg or "hepatic" in msg:
        if "liver_disease" not in state.clinical_context.comorbidities:
            state.clinical_context.comorbidities.append("liver_disease")
            
    if "asthma" in msg or "wheeze" in msg:
        if "asthma" not in state.clinical_context.comorbidities:
            state.clinical_context.comorbidities.append("asthma")
            
    if "pregnant" in msg or "pregnancy" in msg:
        state.clinical_context.pregnancy_status = "pregnant"
        
    return state


def clinical_reasoning_agent(state: PharmacyState) -> PharmacyState:
    """
    Core agent that reasons about medicine suitability based on clinical context.
    Provides structured recommendations or asks clarifying questions.
    """
    print("\n[CLINICAL REASONER] Running evidence-based clinical reasoning...")
    state.turn_count += 1
    
    # 1. Update Context
    state = enrich_context_from_message(state)
    
    # 2. Gather Potential ATC codes/Medicines based on conversation intent
    # If a specific medicine was asked for, we'd look it up here.
    # For now, let's assume we searched for medicines matching the query.
    # In a real flow, this would integrate with the semantic search step earlier.
    # Here we just grab some general stock for the prompt.
    with db.transaction() as tx:
        # Get up to 10 in-stock medicines for LLM to choose from
        available_meds = tx.session.query(Medicine).filter(Medicine.stock > 0).limit(10).all()
        inventory_context = json.dumps([
            {"name": m.name, "atc_code": m.atc_code, "indications": m.indications} 
            for m in available_meds
        ], indent=2)
        
    # We ideally want to check the specific proposed meds, but let the LLM suggest first based on inventory.
    # In a more robust pipeline, we'd query DB for meds matching symptoms, THEN run contraindication checks, 
    # THEN pass to LLM.
    
    # Format the prompt
    system_prompt = CLINICAL_SYSTEM_PROMPT.format(
        clinical_context=state.clinical_context.model_dump_json(indent=2),
        contraindications="To be verified against LLM recommendation.",
        interactions="To be verified against LLM recommendation.",
        combinations="Available in DB, check synergistic pairs.",
        inventory_context=inventory_context
    )
    
    response = call_llm(
        system_prompt=system_prompt,
        user_message=state.current_message,
        temperature=0.1  # Low temp for clinical consistency
    )
    
    parsed_response = parse_llm_json(response)
    
    # Log the reasoning
    log_entry = {
        "turn": state.turn_count,
        "action": "clinical_reasoning",
        "reasoning": parsed_response.get("reasoning_chain", []),
        "recommendation": parsed_response.get("primary_recommendation")
    }
    state.reasoning_history.append(log_entry)
    
    # Handle information gaps (Ask user for more info)
    if parsed_response.get("information_gaps") and not parsed_response.get("primary_recommendation"):
        gaps_str = ", ".join(parsed_response["information_gaps"])
        state.response = f"I need a bit more clinical context before recommending a medicine. Could you clarify: {gaps_str}?"
        state.conversation_phase = "intake"
        return state
        
    # Handle valid recommendation
    rec = parsed_response.get("primary_recommendation")
    if rec:
        # Run hard safety checks to verify LLM
        violations = ContraindicationService.check_contraindications(rec.get("atc_code"), state.clinical_context)
        
        if violations:
            # LLM hallucinated an unsafe drug or missed a rule. Override it.
            v = violations[0]
            if v.get("severity") == "absolute":
                state.safety_flags.append(f"CRITICAL: {rec.get('medicine')} is contraindicated due to {v.get('condition')}.")
                state.response = f"I cannot recommend {rec.get('medicine')} because it is unsafe given your {v.get('condition')}. {v.get('reason')} "
                if v.get("alternative_suggestion"):
                    state.response += f"Instead, I suggest {v.get('alternative_suggestion')}."
                return state
                
        # If safe, construct response
        chain_text = "\\n- ".join(parsed_response.get('reasoning_chain', []))
        
        resp_text = f"**Clinical Recommendation: {rec.get('medicine')}**\\n"
        if parsed_response.get("warnings"):
            resp_text += "\\n⚠️ **Clinical Warnings:**\\n- " + "\\n- ".join(parsed_response.get("warnings")) + "\\n"
        
        resp_text += f"\\n*Reasoning:*\\n- {chain_text}\\n"
        
        if parsed_response.get('combinations'):
            # Note: The combination suggestions list should be parsed here if available 
            pass
            
        state.response = resp_text
        
        # Optionally add to order items automatically if confidence is high and we are in building phase
        
    return state
