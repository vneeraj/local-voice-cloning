# Product Guidelines

## UX Principles

1. **One task at a time**: The UI should guide the user through a clear linear flow: pick/upload reference → enter text → generate → download/save. No cognitive overload.
2. **Immediate feedback**: Show loading states, progress indicators, and errors inline. Never leave the user wondering if something is happening.
3. **Forgive mistakes**: Allow re-uploading a reference, re-entering text, or switching profiles without losing work in other fields.
4. **No dead ends**: Every error state should explain what went wrong and offer a clear recovery path.

## Layout & Structure

- **Single-page layout**: No routing, no page reloads. All interactions happen in one view.
- **Two-panel structure** (desktop):
  - **Left panel**: Voice source selection (file upload, YouTube URL, saved profile)
  - **Right panel**: Text input, generate button, output player, and download/save controls
- **Responsive**: Stack panels vertically on narrower viewports (< 768 px).

## Visual Design

- **Aesthetic**: Dark background, minimal chrome. Think audio tool / DAW-inspired — not a generic web app.
- **Color palette**:
  - Background: `#0f0f0f`
  - Surface: `#1a1a1a` (cards/panels)
  - Border: `#2a2a2a`
  - Accent: `#6c63ff` (purple) — primary actions
  - Success: `#22c55e`
  - Error: `#ef4444`
  - Text primary: `#f5f5f5`
  - Text muted: `#888888`
- **Typography**: System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`). No web font downloads.
- **Border radius**: 8 px for cards, 6 px for inputs/buttons.
- **Spacing**: 8 px grid.

## Component Behavior

### Reference Audio Panel
- File drop zone: drag-and-drop or click to pick. Show filename + waveform thumbnail (or duration) on success.
- YouTube field: text input + "Extract" button. Show spinner during download. Show extracted clip duration on success.
- Profile picker: searchable dropdown list of saved profiles. Show a "Preview" play button next to each.
- Only one source active at a time; switching clears the previous selection.

### Text Input
- Multi-line textarea, min 4 rows.
- Character count indicator (F5-TTS works best under ~500 characters per synthesis; warn above 400).
- "Generate" button disabled until a reference source is active and text is non-empty.

### Generation
- Show a progress spinner with a status message ("Cloning voice…", "Synthesizing speech…") during inference.
- On completion: show an in-page `<audio>` player. Auto-play is OFF by default.
- Provide a "Download WAV" button.
- Provide a "Save as Profile" button that opens a small modal (name input + save).

### Profile Library
- Collapsible panel at the bottom (or sidebar on wide screens).
- Each profile card: name, creation date, "Use this voice" button, delete icon.
- Delete requires a confirmation prompt (inline, not a browser alert).

## Accessibility

- All interactive elements must be keyboard-navigable (Tab, Enter, Space).
- ARIA labels on icon-only buttons.
- Color is never the sole indicator of state (also use text or icons).
- Minimum touch target: 44 × 44 px.

## Performance Targets

- Initial page load: < 2 s (app is local, so this is trivially achievable).
- F5-TTS inference: target < 60 s for a 100-word sentence on M5 MPS.
- Frontend bundle size: < 500 KB gzipped.
- No UI jank during inference (use async API calls, never block the main thread).

## Error Handling UX

- API errors: show a dismissible error banner with the server's error message.
- File format errors: show inline below the drop zone.
- YouTube download failures: show inline with a suggestion (e.g., "Try a shorter clip or a public video").
- Network errors: generic "Could not reach the server. Is the app running?" message.
