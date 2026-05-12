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

- [x] Phase 6.1: Add function to trigger hand inpainting workflow.
- [x] Phase 6.2: Pass selected candidate and mask to hand workflow.
- [x] Phase 6.3: Read hand reference outputs from output folder.
- [x] Phase 6.4: Show hand reference thumbnails in UI.
- [x] Phase 6.5: Handle failed hand generation gracefully.

## Phase 7: Save and Export

- [x] Phase 7.1: Save project metadata (`project.json`).
- [x] Phase 7.2: Save prediction metadata (`predictions.json`).
- [x] Phase 7.3: Save hand reference metadata (`hand_refs.json`).
- [x] Phase 7.4: Export simple hand reference sheet image.
- [x] Phase 7.5: Add save/export confirmation UI.

## Later / Optional

- [x] Improve thumbnail layout.
- [x] Add regenerate prediction button.
- [x] Add regenerate hand reference button.
- [x] Add clearer error messages.
- [x] Add simple project reopen support.
- [x] Add clear project summary.
- [x] Add ComfyUI workflow requirements guide.
- [x] Add local workflow placeholder validation helper.
- [x] Add workflow placeholder validation UI.
- [x] Add local AI setup guide.
- [x] Document post-AI setup implementation plan.

## Phase 9: Real Local AI Workflow Check

- [ ] Phase 9.1: Verify the prediction workflow actually uses the color rough image input.
- [ ] Phase 9.2: Document the minimum recommended prediction workflow structure for img2img or ControlNet.
- [ ] Phase 9.3: Verify the hand inpainting workflow actually uses both selected candidate and mask image.
- [ ] Phase 9.4: Add beginner-friendly workflow mismatch messages if ComfyUI accepts a prompt but the workflow ignores the image input.

## Phase 10: Generation Completion and Output Pickup

- [ ] Phase 10.1: Store the latest prediction prompt ID after queueing.
- [ ] Phase 10.2: Add a minimal ComfyUI history lookup function for a prompt ID.
- [ ] Phase 10.3: Detect finished prediction outputs from ComfyUI history.
- [ ] Phase 10.4: Copy finished prediction images into `project_output/predictions/`.
- [ ] Phase 10.5: Refresh prediction thumbnails after copied outputs are available.
- [ ] Phase 10.6: Store the latest hand reference prompt ID after queueing.
- [ ] Phase 10.7: Detect finished hand reference outputs from ComfyUI history.
- [ ] Phase 10.8: Copy finished hand reference images into `project_output/hand_refs/`.
- [ ] Phase 10.9: Refresh hand reference thumbnails after copied outputs are available.

## Phase 11: Beginner-Friendly Generation Flow

- [ ] Phase 11.1: Add simple waiting/status messages for queued generation.
- [ ] Phase 11.2: Add clearer message when ComfyUI is not running or unreachable.
- [ ] Phase 11.3: Add clearer message when workflow placeholders are present but image input is not connected in the workflow.
- [ ] Phase 11.4: Add guard message before hand reference generation if selected candidate or mask is missing.
- [ ] Phase 11.5: Add a simple troubleshooting checklist to the local AI setup guide.

## Phase 12: v0.1 Validation

- [ ] Phase 12.1: Run one complete manual prediction test with external ComfyUI.
- [ ] Phase 12.2: Run one complete manual hand reference test with external ComfyUI.
- [ ] Phase 12.3: Confirm sheet export and metadata after a full workflow.
- [ ] Phase 12.4: Update docs with final v0.1 known issues and usage steps.
