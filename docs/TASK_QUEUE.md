# Color Rough Reference Tool - Task Queue

Codex should work on the next unfinished task only unless the user says otherwise.

## Phase 0: Foundation

- [x] Phase 0.1: Inspect the current project structure without changing code.
- [x] Phase 0.2: Create or confirm project folder structure for the standalone app.
- [x] Phase 0.3: Add basic settings storage.
- [x] Phase 0.4: Add output folder creation logic.
- [x] Phase 0.5: Add workflow file placeholder handling.

## Phase 1: Color Rough Input

- [x] Phase 1.1: Add color rough image selection.
- [x] Phase 1.2: Add input preview.
- [x] Phase 1.3: Add input image copy/save into project output.
- [x] Phase 1.4: Validate supported image formats.

## Phase 2: ComfyUI Configuration

- [x] Phase 2.1: Add UI/settings field for ComfyUI path or endpoint.
- [x] Phase 2.2: Add UI/settings field for prediction workflow file.
- [x] Phase 2.3: Add UI/settings field for hand inpainting workflow file.
- [x] Phase 2.4: Add ComfyUI configuration test.
- [x] Phase 2.5: Save settings snapshot metadata.
- [x] Phase 2.6: Add minimal app entry point and basic settings/input UI shell.

## Phase 3: Prediction Generation

- [x] Phase 3.1: Add function to trigger prediction workflow.
- [x] Phase 3.2: Pass input color rough to prediction workflow.
- [x] Phase 3.3: Read prediction outputs from output folder.
- [x] Phase 3.4: Show prediction thumbnails in UI.
- [x] Phase 3.5: Handle missing or failed generation outputs gracefully.

## Phase 4: Candidate Selection

- [x] Phase 4.1: Add prediction candidate selection UI.
- [x] Phase 4.2: Save selected candidate into `selected/`.
- [x] Phase 4.3: Store selected candidate in metadata.

## Phase 5: Hand Mask Editing

- [x] Phase 5.1: Display selected candidate for mask editing.
- [x] Phase 5.2: Add simple hand mask drawing tool.
- [x] Phase 5.3: Add simple rectangle-based mask option (optional if easy).
- [x] Phase 5.4: Save mask image into `masks/`.

## Phase 6: Hand Reference Generation

- [ ] Phase 6.1: Add function to trigger hand inpainting workflow.
- [ ] Phase 6.2: Pass selected candidate and mask to hand workflow.
- [ ] Phase 6.3: Read hand reference outputs from output folder.
- [ ] Phase 6.4: Show hand reference thumbnails in UI.
- [ ] Phase 6.5: Handle failed hand generation gracefully.

## Phase 7: Save and Export

- [ ] Phase 7.1: Save project metadata (`project.json`).
- [ ] Phase 7.2: Save prediction metadata (`predictions.json`).
- [ ] Phase 7.3: Save hand reference metadata (`hand_refs.json`).
- [ ] Phase 7.4: Export simple hand reference sheet image.
- [ ] Phase 7.5: Add save/export confirmation UI.

## Later / Optional

- [ ] Improve thumbnail layout.
- [ ] Add regenerate prediction button.
- [ ] Add regenerate hand reference button.
- [ ] Add clearer error messages.
- [ ] Add simple project reopen support.
