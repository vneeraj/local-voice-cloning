# Track 02 Specification: React Frontend

## Goal

Build the complete VoiceForge single-page React application — the full production UI that replaces the placeholder `App.tsx` from Track 01. After this track the app is feature-complete and shippable.

## Scope

### Components & Pages

The UI is a single page with three logical regions:

#### 1. Left Panel — Voice Source
Manages which voice reference is active. Only one source mode is active at a time; switching clears the others.

**File Upload tab**
- Drag-and-drop zone + click-to-browse for WAV / MP3 / FLAC / OGG / M4A / AAC
- Shows filename and duration on success
- Inline error on unsupported format or upload failure
- Calls `POST /api/upload_reference` → stores `reference_id` in state

**YouTube tab**
- URL text input + "Extract" button
- Spinner during extraction (can take 10–30 s)
- Shows extracted clip info (or error) inline
- Calls `POST /api/upload_youtube` → stores `reference_id` in state

**Saved Profiles tab**
- Searchable list of profiles from `GET /api/profiles`
- Each row: profile name, creation date, play-preview button (streams `/api/profiles/{id}/audio`), "Use" button, delete icon
- Delete prompts an inline confirmation (not a browser `alert`)
- Selecting a profile sets `reference_id` = profile's `reference_id`

#### 2. Right Panel — Generate
- Multi-line textarea for input text
- Character count indicator; warn (yellow) above 400 chars
- "Generate" button — disabled until reference source active + text non-empty
- Spinner + status message during inference ("Cloning voice…")
- On success: `<audio>` player (no autoplay) + "Download WAV" link
- "Save as Profile" button opens modal

#### 3. Save Profile Modal
- Name text input
- "Save" button — calls `POST /api/profiles` with `name` + `reference_id`
- On success: closes modal, refreshes profile list, shows brief success toast
- Inline validation: name required

#### 4. Global Toast Notifications
- Dismissible banners for API errors and success messages
- Auto-dismiss after 4 s

### API Client

A typed `src/api.ts` module wraps all fetch calls and throws a consistent `ApiError` with `message` and `status` on non-2xx responses.

### Styling

- CSS custom properties (variables) for the full design token set from `product-guidelines.md`
- CSS Modules per component (`.module.css`)
- Global reset + base styles in `src/index.css`
- Responsive: two-column on ≥ 768 px, single-column below
- No external CSS framework

### Testing

- Vitest + React Testing Library for all components
- Mock `fetch` globally in test setup
- Test each component's happy path and primary error state

## Acceptance Criteria

- User can upload a local audio file, type text, and download a generated WAV — end to end
- User can paste a YouTube URL, wait for extraction, then generate speech
- User can save a generated voice as a profile and reuse it on reload
- User can delete a profile with inline confirmation
- All UI states (loading, error, empty, success) are visually distinct
- No browser `alert` / `confirm` / `prompt` calls
- Character count warns above 400, does not block submission
- App works at 375 px width (iPhone SE) and 1280 px (desktop)
- All component tests pass; frontend coverage ≥ 80%

## Out of Scope

- Browser microphone recording (future track)
- Waveform visualisation (future track)
- Multi-language UI
- User accounts / authentication
