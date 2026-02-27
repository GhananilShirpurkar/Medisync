# PLAN-landing-redesign

## 1. Context & Goal

The user feels the current multi-box landing page (`/`) forces unnecessary pre-categorization (Describe Symptoms, Upload Prescription, Search Medicine).
The goal is to abolish the 4-box layout and drop the user straight into a **Unified AI Kiosk** at the root route (`/`). The design language must strictly adhere to **Minimalist Zen**: generous whitespace, warm typography, sage greens/warm greys, and organic micro-interactions (no high-tech/clinical sci-fi aesthetics and absolutely no purple). Additionally, the order history/cart should become a persistent, peripheral sliding sidebar rather than a standalone page.

## 2. Proposed Changes

### 2.1 Routing & Architecture

- **[MODIFY] `frontend/src/App.jsx`**: Change the `/` route to render the new `Kiosk` interface instead of the old `Landing` page. Remove redundant routes like `/prescription` and `/kiosk` if they are fully merged into the home view.

### 2.2 Unified Kiosk Interface (Minimalist Zen)

- **[MODIFY] `frontend/src/pages/Landing.jsx`** (or replace with Kiosk):
  - Strip out the current 4 quick-action cards.
  - Implement a clean, breathing layout.
  - Background: Warm greys (e.g., `#F7F7F5`).
  - Typography: Human-scale, warm fonts.
  - Integrate `OrderPanel` directly into the center of the screen with a focus on negative space.
- **[MODIFY] `frontend/src/components/OrderPanel.jsx`**:
  - **Unified Input Bar**: Combine the text input, the `VoiceInputButton`, and a new `PrescriptionUploadButton` (which will trigger the existing `CameraModal` logic but from within the chat context) into a single, cohesive, floating input capsule at the bottom.
  - Add organic micro-interactions (e.g., subtle glow on focus, soft scale on hover) using Tailwind transitions.
  - Update the color palette of chat bubbles: Sage greens for AI responses, muted warm tones for user messages.

### 2.3 Peripheral Cart / Orders Sidebar

- **[NEW] `frontend/src/components/SidebarCart.jsx`**:
  - Create a sliding sidebar component positioned on the right edge of the screen.
  - **Collapsed State**: A thin vertical strip or floating action button with a subtle badge indicating the number of items/orders.
  - **Expanded State**: Slides out to reveal the current cart and quick links to past orders.
  - **Mobile Behavior**: Turns into a bottom-sheet drag-up menu on small screens.
  - Integrate this sidebar into the main layout wrapper or directly inside the unified Kiosk view.

## 3. Verification Plan

### Manual Verification

1. **Routing**: Navigate to `localhost:5173/`. Verify that the app drops the user immediately into the chat interface without any intermediate box-selection page.
2. **Aesthetic Check**: Verify the colors (Sage green, warm grey) and typography. Ensure the "Minimalist Zen" vibe is achieved (no sharp neon borders, no bento grids, no purple).
3. **Unified Input**: Test that typing text, speaking via the mic icon, and clicking the paperclip/camera icon all work correctly from the single input bar. Uploading an image should append a message to the chat and trigger the Orchestration workflow.
4. **Sidebar Interaction**: Verify the sidebar is collapsed by default. Submitting an order should update the badge count. Clicking the badge should smoothly slide out the sidebar showing cart contents. Test responsiveness (bottom sheet on mobile).
