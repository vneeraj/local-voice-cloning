# Track 02 Implementation Plan: React Frontend

## Phase 1: Foundation — Styles, Types & API Client

- [ ] Write `src/index.css` — CSS reset, design tokens (color/spacing/radius vars), base typography
- [ ] Write `src/api.ts` — typed fetch wrapper, `ApiError` class, all 7 endpoint functions:
  - `uploadReference(file: File): Promise<{ reference_id, preview_url }>`
  - `uploadYoutube(url: string): Promise<{ reference_id, preview_url }>`
  - `generate(text: string, reference_id: string): Promise<Blob>`
  - `listProfiles(): Promise<Profile[]>`
  - `saveProfile(name: string, reference_id: string): Promise<Profile>`
  - `getProfileAudioUrl(profile_id: string): string`
  - `deleteProfile(profile_id: string): Promise<void>`
- [ ] Write `src/types.ts` — `Profile`, `ReferenceSource`, `GenerationStatus` shared types
- [ ] Write `src/api.test.ts` — unit tests for `ApiError` and each api function (mock `fetch`)

## Phase 2: Global UI Primitives

- [ ] `src/components/Toast/Toast.tsx` + `Toast.module.css` — dismissible notification banner (success / error variants)
- [ ] `src/components/Toast/useToast.ts` — hook: `{ toasts, addToast, removeToast }`
- [ ] `src/components/Spinner/Spinner.tsx` + `Spinner.module.css` — animated loading indicator
- [ ] `src/components/Modal/Modal.tsx` + `Modal.module.css` — accessible focus-trapped overlay
- [ ] `src/components/Toast/Toast.test.tsx` — renders, auto-dismisses, dismiss on click
- [ ] `src/components/Modal/Modal.test.tsx` — renders children, closes on backdrop click, traps focus

## Phase 3: Left Panel — Voice Source

- [ ] `src/components/VoiceSource/VoiceSourcePanel.tsx` + `.module.css`
  - Tab bar: "Upload File" | "YouTube" | "Saved Profiles"
  - Manages active tab state; renders child panels
- [ ] `src/components/VoiceSource/FileUploadTab.tsx` + `.module.css`
  - Drag-and-drop zone (`onDragOver`, `onDrop`, `onClick` → hidden `<input type="file">`)
  - Accepted formats label
  - Upload progress / success / error state
  - On success: shows filename + calls `onReferenceReady(reference_id, preview_url)`
- [ ] `src/components/VoiceSource/YouTubeTab.tsx` + `.module.css`
  - URL input + Extract button
  - Loading spinner during extraction
  - Success/error state display
  - On success: calls `onReferenceReady(reference_id, preview_url)`
- [ ] `src/components/VoiceSource/ProfilesTab.tsx` + `.module.css`
  - Fetches profile list on mount (and after save/delete)
  - Search/filter input
  - Profile row: name, date, preview play button, "Use" button, delete icon
  - Inline delete confirmation ("Are you sure? Yes / Cancel")
  - On "Use": calls `onReferenceReady(reference_id, preview_url)`
- [ ] `src/components/VoiceSource/FileUploadTab.test.tsx`
- [ ] `src/components/VoiceSource/YouTubeTab.test.tsx`
- [ ] `src/components/VoiceSource/ProfilesTab.test.tsx`

## Phase 4: Right Panel — Generate

- [ ] `src/components/Generate/GeneratePanel.tsx` + `.module.css`
  - Textarea with char count (warns yellow > 400)
  - "Generate" button (disabled when no reference or empty text)
  - Spinner + "Cloning voice…" status during inference
  - Calls `generate(text, reference_id)` → receives Blob
  - Creates object URL from Blob for playback and download
- [ ] `src/components/Generate/AudioPlayer.tsx` + `.module.css`
  - Native `<audio>` element (no autoplay)
  - Download WAV button (anchor with `download` attribute)
  - "Save as Profile" button → opens SaveProfileModal
- [ ] `src/components/Generate/SaveProfileModal.tsx` + `.module.css`
  - Name input + Save / Cancel
  - Calls `saveProfile(name, reference_id)`
  - On success: closes, triggers profile list refresh, fires success toast
  - Inline validation: empty name blocked
- [ ] `src/components/Generate/GeneratePanel.test.tsx`
- [ ] `src/components/Generate/AudioPlayer.test.tsx`
- [ ] `src/components/Generate/SaveProfileModal.test.tsx`

## Phase 5: App Shell & Integration

- [ ] `src/App.tsx` — full app layout:
  - `ToastProvider` context wrapping everything
  - Two-column layout (left: `VoiceSourcePanel`, right: `GeneratePanel`)
  - Shared state: `referenceId`, `referencePreviewUrl` lifted to App; passed down as props
  - Profile refresh callback: passed from App → `SaveProfileModal` → `ProfilesTab`
- [ ] `src/App.module.css` — two-column grid, responsive breakpoint at 768 px
- [ ] `src/App.test.tsx` — integration: renders both panels, reference selection propagates to generate button
- [ ] Run `npm run build` — verify zero TypeScript errors, bundle < 500 KB

## Phase 6: Validation

- [ ] `npm run test -- --coverage --run` — all tests pass, coverage ≥ 80%
- [ ] `npm run lint` — zero ESLint errors
- [ ] `npm run build` — clean production build
- [ ] Manual smoke test on Mac: upload file → generate → download
- [ ] Manual smoke test: YouTube URL → generate → save profile → reuse profile → delete profile
- [ ] Responsive check: 375 px and 1280 px widths
