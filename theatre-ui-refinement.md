# Theatre UI Refinement

## Context

The Operating Theatre UI requires adjustments based on the user's feedback:

- Agent reasoning logs should become the primary content on the left side, replacing the static timeline.
- Timeline should slide out when "History" is triggered.
- Add live telemetry and confidence data on the right side.
- Handle state variations correctly (empty, active, zero).

## Design Commitment

🎨 **DESIGN COMMITMENT: NEON BRUTALIST MEDICAL**

- **Topological Choice:** We are moving the "Chronological History" entirely out of the standard viewport flow (pushing it to an overlay) to make room for _Agent Logs_ as a continuous vertical narrative. The layout shifts from a static split to a high-density, terminal-like observation room.
- **Risk Factor:** Relegating typical "EHR Timeline" data to a triggered drawer is unconventional in medical UI. We are prioritizing machine-driven action over historical static data.
- **Readability Conflict:** We embrace the monospace density of logs and telemetry data, trusting the "Theatre" clinical persona rather than simplifying to soft "bento" cards.
- **Cliché Liquidation:** Killing off padded white cards and muted blues/purples. We will use stark, sharp edges, dashed lines, and raw colors like `--amber`, `--green`, and monochrome text to simulate an intense diagnostic deck.

## Implementation Steps

### Phase 1: Left Zone (Agent Traces)

- `TheatrePage.jsx`: Replace left zone static `IntelligenceTrace` with an animated, stylized step component.
- Ensure the `[📋 History]` sliding trigger actually works correctly. It seems the overlay might be blocking or `z-index` is an issue in `TheatreLayout.css` (will fix `.panel-backdrop`).
- Add active step pulsing animations.

### Phase 2: Right Zone (Fusion Metrics)

- `TheatrePage.jsx`: Replace right zone "FUSION CONFIDENCE" mock text with dynamic elements.
- Implement circular progress ring CSS in `.theatre-layout-container` or inline.
- Implement breakdown progress bars for Voice/Vision/Text.
- Handle "Empty States" explicitly (e.g., dashed ring if no data).

### Phase 3: Center Column (Conversation Stage)

- `ConsultationStage.jsx`: Add an idle state when there are `0` messages. This should show a centered watermark, "How can I help you today?".
- Improve input bar visual density with icon elements.
- Ensure proper scrolling using `min-height: 0` constraints.

### Phase 4: Data Integration

- Map `pipelineState` values to these new UI components to show real-time changes where possible. Default mock parameters if backend not sending them yet.
