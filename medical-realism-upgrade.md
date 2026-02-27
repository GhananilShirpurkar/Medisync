# Medical Realism Upgrade — Implementation Plan

## Overview

Elevate MediSync from a similarity-matching tool to a clinically aware pharmacy agent. This upgrade implements structured dosage extraction, synergistic combination validation, generic-first inventory logic, and explicit user consent for order creation.

## User Review Required

> [!IMPORTANT]
> **Orchestration Change**: The `agent_graph` will now terminate at the recommendation stage. Orders will be held in a "Pending Consent" state and only written to the database after the user explicitly says "Confirm" or "Place Order".

## Proposed Changes

### 1. Context & NLP (Front Desk Agent)

**Objective**: Extract quantitative dosage parameters for precise billing.

#### [MODIFY] [front_desk_agent.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/agents/front_desk_agent.py)

- Refine `extract_patient_context` prompt to capture:
  - `dose_units`: (Integer) e.g., "1 tablet", "2 days"
  - `frequency`: (Integer) Number of times per day
  - `duration`: (Integer) Number of days
- **Specialist Rule**: Implement a schema-first extraction using Pydantic-like JSON structures to ensure `None` is handled correctly.

#### [MODIFY] [state.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/state.py)

- Update `OrderItem` to include `units_per_dose`, `frequency_daily`, and `total_days`.

---

### 2. Clinical Intelligence (Medical Validator)

**Objective**: Move beyond simple safety to "intellectual" synergy.

#### [MODIFY] [medical_validator_agent.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/agents/medical_validator_agent.py)

- **Combination Check**: Update the LLM prompt to check for _synergy_ (e.g., "If prescribing NSAID, suggest an antacid for gastric protection").
- **Reasoning Trace**: Add `clinical_rationale` to the state to show the user "Why" this combination was suggested.

#### [MODIFY] [inventory_service.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/services/inventory_service.py)

- **Generic-First Logic**:
  1. Check if the exact requested medicine is OOS.
  2. If OOS, first query the `generic_equivalent` column for exact matches.
  3. Only if no generic exists, fall back to "Similar Medicines" (embedding search).

---

### 3. Order Flow (Fulfillment & Graph)

**Objective**: Explicit consent and accurate billing.

#### [MODIFY] [graph.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/graph.py)

- Truncate the entry graph at `inventory`.
- `fulfillment` node becomes a "Manual Trigger" agent.

#### [MODIFY] [conversation.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/routes/conversation.py)

- Add "Order Consent" state detection.
- If user message matches "confirm", "yes", or "place order", manually invoke the `fulfillment_agent` with the current state.

#### [MODIFY] [fulfillment_agent.py](file:///home/koanoir/Desktop/Projects/01_sandbox/Medisync/backend/src/agents/fulfillment_agent.py)

- **Billing Logic**: Total Quantity = `units_per_dose` _ `frequency_daily` _ `total_days`.
- Calculate `total_amount` based on this derived quantity.

## Verification Plan

### Automated

1. **Dosage Test**: `api_post` symptoms "1 tab twice a day for 5 days" → Verify `extracted_items` has `quantity_total=10`.
2. **Generic Test**: Mark "Advil" OOS, set "Generic=Ibuprofen". Query Advil → Verify Ibuprofen is suggested with "Generic Match" flag.
3. **Consent Test**: Query symptoms → Verify `order_id` is still `null`. Send "Place order" → Verify `order_id` is generated.

### Manual

- "I have a sharp back pain, need something for 7 days."
- Observe: System should suggest Painkiller + Gastric protection (Antacid).
- Observe: "Confirm these 14 tablets?"
- Say "Yes" and check DB.
