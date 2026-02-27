# PLAN-glass-desk-ecosystem

## 1. Context & Goal

The previous "Minimalist Zen" layout still relied on a linear chat-bubble feed, which enforces a "User ↔ Chatbot" paradigm.
MediSync is a Multi-Agent Ecosystem. The new goal is to implement the **"Glass Desk" (Universal Input Topology)**.

### Core Paradigm Shift:

- **No linear chat.** No "user message" followed by "assistant message".
- **Spatial Object Model.** Every input (voice, text, image) creates a tangible "Work Object" (a card/panel) on an infinite-feeling canvas.
- **Agent Annotations.** Agents (Vision, Medical, Inventory) do not "reply" in a chat; they _annotate_ and _augment_ the Work Objects directly (using sticky notes, highlights, and status badges).
- **Proximity = Context.** Dragging or placing objects near each other triggers cross-agent synthesis (e.g., connecting a Lab Result object to a Prescription object).

## 2. Structural Topology

The `Kiosk` replaces the linear `AppLayout` with a universal spatial canvas.

### 2.1 The Canvas (`WorkspaceCanvas.jsx`)

- Replaces the scrolling message feed.
- An expansive area (e.g., a subtle dot-grid or pure minimalist `#F7F7F5` background).
- Manages an array of `WorkObjects` with X/Y coordinates (or a flexible CSS Grid/Masonry layout if drag-and-drop is too complex for V1).

### 2.2 The Omni-Bar (`OmniInputBar.jsx`)

- Replaces `OrderPanel`'s bottom input form.
- A floating capsule (bottom center) that accepts Text, Voice, or File Drops.
- **Action**: Submitting from the Omni-Bar instantly spawns a new `WorkObject` onto the Canvas.

### 2.3 Work Objects (`WorkObject.jsx`)

A polymorphic component that renders differently based on the input modality:

- **`DocumentArtifact`**: Rendered when an image/prescription is uploaded. Features zoom/pan.
- **`TranscriptCard`**: Rendered for voice/text input. Shows the raw text, intent, and live audio waveform if applicable.
- **`DataPanel`**: Rendered when structured lab results are pasted.

### 2.4 Agent Annotations (The "Ecosystem" Layer)

Instead of returning a single JSON "message", the backend orchestrator should return a payload of _Annotations_.

- **Vision Agent**: Overlays blue highlights on the `DocumentArtifact`.
- **Medical Agent**: Renders as a "Sticky Note" (e.g., amber warning for allergies) attached to the side of a Work Object.
- **Inventory/Cart Agent**: Renders as a Price Tag/Stock Badge directly on the extracted medicine names inside the Work Object.
- **Connections**: SVG `<path>` lines (glowing threads) rendered between related Work Objects when synthesis occurs.

## 3. Implementation Steps (Frontend V1)

To transition from our current state to the Glass Desk without breaking everything, we will do this iteratively:

1. **Phase 1: Kill the Chat Feed.**
   - Rename `OrderPanel.jsx` to `OmniInputBar.jsx`. Extract just the floating input capsule.
   - Create `WorkspaceCanvas.jsx` to replace the scrolling message list.
2. **Phase 2: The Object Model.**
   - Instead of appending `{ role: 'user', content: ... }` to a state array, append `{ id, type: 'transcript|document', payload: {...}, annotations: [] }`.
   - Build the base `WorkObject` card to display these items as distinct, standalone blocks on the screen (using CSS Grid/Flex wrap for V1, avoiding full D&D overhead initially).
3. **Phase 3: Agent Overlays.**
   - Update the backend response handling so that when the Orchestrator replies, it updates the `annotations` array of the specific `WorkObject`, rather than spawning a new "Assistant" chat bubble.
   - Render these annotations as badges, sticky notes, or inline highlights on the card.
4. **Phase 4: Synthesis UI (Optional V2).**
   - Add SVG lines connecting cards based on agent reasoning.

## 4. Verification

- Navigating to `/` shows an empty canvas and the Omni-Bar.
- Typing "I have a headache" spawns a `TranscriptCard` in the center of the canvas.
- 2 seconds later, the Triage Agent attaches an amber "Urgency: Low" badge to that card, and the Inventory Agent attaches a "Paracetamol: In Stock" tag.
- Uploading a prescription spawns a `DocumentArtifact` next to it, which gets annotated by the Vision Agent.
- Absolutely NO chat bubbles `(User: ... | Assistant: ...)` are rendered.
