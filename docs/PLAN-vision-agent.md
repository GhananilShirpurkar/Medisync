# PLAN-vision-agent

## 1. Context & Goal

The user wants to improve the Vision Agent and everything regarding prescription uploads. Current issues include timeouts and poor integration with the UI where medicines extracted are not rendered fully.

## 2. Core Components to Address

- **VisionAgent (`backend/src/agents/vision_agent.py`)**
  - Dependency on `gemini-2.0-flash-exp` might be slow or unstable causing timeouts.
  - Needs better structured JSON schema constraints.
- **OrchestrationService (`backend/src/services/orchestration_service.py`)**
  - Should actively query `MedicalValidationAgent` and `InventoryAndRulesAgent` properly.
  - Return structure must match frontend expectations closely.
- **Frontend UI (`frontend/src/components/OrderPanel.jsx` & `CameraModal.jsx`)**
  - Enhance feedback loops for successful uploads.
  - Populate conversational UI with extracted medicines instead of keeping them hidden.
  - Handle out-of-stock scenarios gracefully.

## 3. Tasks Breakdown

- [ ] Upgrade Gemini Vision to stable model or implement retry mechanism for `gemini-2.0-flash`.
- [ ] Connect Orchestration Service to real InventoryService correctly (done but check UI handling).
- [ ] Update frontend state management in `OrderPanel.jsx` to render the extracted medicines and add them to order.
- [ ] Ensure seamless message passing from `OrderPanel` to `ConversationalInterface`.
- [ ] Add loading skeletons during the 20s-60s OCR wait time.

## 4. Verification

- Verify that taking a photo parses medicines within 60s.
- Verify the UI reflects extracted medicines.
- Verify timeouts do not crash the app silently.
