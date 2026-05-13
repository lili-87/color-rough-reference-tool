# Color Rough Reference Tool - Status

## Current Direction

This project is a standalone tool for:

```text
Color rough
↓
Prediction generation
↓
Candidate selection
↓
Hand mask creation
↓
Hand reference generation
↓
Save / export
```

The software is not connected to LaughRef.

---

## Current AI Policy

- Local models only
- No paid APIs
- No cloud dependency in the initial version
- ComfyUI is external
- Models are external
- The software only triggers workflows and manages outputs

Expected generation stack:

- ComfyUI
- SDXL anime-style local model
- ControlNet / img2img
- SDXL Inpainting

---

## Current State

Documentation baseline created.

The repository now has a minimal application folder structure.

Current structure:

```text
src/
└ color_rough_ref_tool/
   ├ core/
   ├ integrations/
   │  └ comfyui/
   └ ui/
tests/
docs/
```

Basic settings storage now exists in `src/color_rough_ref_tool/core/settings.py`.
It can load default settings when no settings file exists and save user settings as JSON.
The default local settings path is `settings/settings.json`, which is ignored by Git.
It can now validate and update the ComfyUI endpoint setting.
It can now validate and update the prediction workflow file setting.
It can now validate and update the hand inpainting workflow file setting.
It can now run a minimal ComfyUI configuration check for the endpoint and workflow file settings.
It can now save the current settings snapshot to `project_output/metadata/settings_snapshot.json`.
It now has a minimal Tkinter app entry point and basic UI shell for selecting a color rough image, editing settings, checking settings, saving settings, and saving a settings snapshot.

Project output folder creation now exists in `src/color_rough_ref_tool/core/project_output.py`.
It creates the standard `project_output` subfolders: `input`, `predictions`, `selected`, `masks`, `hand_refs`, `sheets`, and `metadata`.
Minimal project metadata saving now exists in `src/color_rough_ref_tool/core/project_metadata.py`.
It can save `project_output/metadata/project.json` with the project root, schema version, application name, and creation timestamp.
Minimal prediction metadata saving now exists in `src/color_rough_ref_tool/core/prediction_metadata.py`.
It can save `project_output/metadata/predictions.json` with prediction image file names, paths, sizes, and modified times.
Minimal hand reference metadata saving now exists in `src/color_rough_ref_tool/core/hand_reference_metadata.py`.
It can save `project_output/metadata/hand_refs.json` with hand reference image file names, paths, sizes, and modified times.
Minimal hand reference sheet export now exists in `src/color_rough_ref_tool/core/hand_reference_sheet.py`.
It can arrange saved PNG hand reference images into a simple sheet at `project_output/sheets/hand_sheet_001.png`.

Workflow placeholder handling now exists in `src/color_rough_ref_tool/integrations/comfyui/workflow_placeholders.py`.
The default workflow file locations are:

```text
workflows/prediction_workflow.json
workflows/hand_inpainting_workflow.json
```

These are placeholders for user-provided ComfyUI workflow JSON files.
They do not include ComfyUI, models, checkpoints, paid APIs, or cloud execution.
The same module can now locally check whether workflow JSON contains the placeholders needed for prediction input and hand inpainting input.

Minimal prediction workflow triggering now exists in `src/color_rough_ref_tool/integrations/comfyui/prediction.py`.
It can load the configured prediction workflow JSON and send it to an external ComfyUI `/prompt` endpoint.
It can now replace color rough placeholders in the prediction workflow with the selected color rough image path before sending the prompt.
The supported workflow placeholder strings are `{{COLOR_ROUGH_IMAGE_PATH}}` and `{{COLOR_ROUGH_IMAGE}}`.
It can now read generated prediction image files from a prediction output folder.
Supported prediction output image formats are `png`, `jpg`, `jpeg`, and `webp`.
It does not wait for generation completion yet.
The minimal UI can now load prediction outputs from `project_output/predictions` and show them in a simple prediction output area.
Images that Tkinter can preview are shown as small thumbnails; unsupported preview formats still appear by file name.
Thumbnail cards now use a slightly clearer three-column layout with compact file names and file size labels.
The minimal UI can now queue the prediction workflow again from a selected color rough using the existing prediction trigger.
After queueing a prediction workflow, the minimal UI now saves the latest prediction prompt ID to `project_output/metadata/latest_prediction_prompt.json`.
The prediction integration can now fetch ComfyUI history once for a prompt ID, including the latest saved prediction prompt ID.
The prediction integration can now inspect ComfyUI history to detect whether a prediction prompt is completed and list reported prediction image outputs.
The prediction integration can now copy completed prediction images reported by ComfyUI history from a ComfyUI output folder into `project_output/predictions`.
The minimal UI can now refresh prediction thumbnails from `project_output/predictions` after copied prediction outputs are available.
After queueing prediction generation, the minimal UI now explains that ComfyUI is generating, the prompt ID was saved for history checking, and the user should press Load predictions after ComfyUI finishes.
If prediction images are not available during manual loading, the UI now explains that generation may still be running and the user can wait and press Load predictions again.
Missing, empty, or invalid prediction output folders are now handled with simple status messages instead of crashing the UI.
The minimal UI can now select one loaded prediction candidate with a radio button and show the selected file name in the status area.
The minimal UI can now copy the selected prediction candidate into `project_output/selected` while keeping the original file name.
It now saves minimal selected-candidate metadata to `project_output/metadata/selected_candidate.json`.
The minimal UI can now load the saved selected candidate metadata and show the selected candidate in a simple mask editing preview area.
The mask editing preview now has a minimal brush tool for drawing red mask strokes on the displayed selected candidate.
The mask editing preview now also has a minimal rectangle tool for marking a rectangular mask area on the displayed selected candidate.
The minimal UI can now save the drawn brush and rectangle mask as a black-and-white PNG in `project_output/masks`.
UI error dialogs now add beginner-friendly hints before showing the original technical detail.
When ComfyUI cannot be reached, the UI now tells the user to keep the ComfyUI command window open, open the endpoint in a browser, and check the endpoint URL and port.
Minimal hand inpainting workflow triggering now exists in `src/color_rough_ref_tool/integrations/comfyui/hand_inpainting.py`.
It can load the configured hand inpainting workflow JSON and send it to an external ComfyUI `/prompt` endpoint.
It can now replace selected candidate and hand mask placeholders in the hand inpainting workflow before sending the prompt.
The supported hand workflow placeholder strings are `{{SELECTED_CANDIDATE_IMAGE_PATH}}`, `{{SELECTED_CANDIDATE_IMAGE}}`, `{{HAND_MASK_IMAGE_PATH}}`, and `{{HAND_MASK_IMAGE}}`.
It can now read generated hand reference image files from a hand reference output folder.
Supported hand reference output image formats are `png`, `jpg`, `jpeg`, and `webp`.
It can now fetch ComfyUI history once for the latest saved hand reference prompt ID and inspect whether the hand reference prompt has completed with reported image outputs.
It can now copy completed hand reference images reported by ComfyUI history from a ComfyUI output folder into `project_output/hand_refs`.
The minimal UI can now show hand reference images from `project_output/hand_refs` in a simple thumbnail area.
Images that Tkinter can preview are shown as small thumbnails; unsupported preview formats still appear by file name.
The minimal UI can now refresh hand reference thumbnails from `project_output/hand_refs` after copied hand reference outputs are available.
The minimal UI can now queue the hand inpainting workflow again from the saved selected candidate and saved hand mask.
Before queueing hand reference generation, the UI now checks whether the selected candidate and hand mask are saved and tells the user which step to do next if either one is missing.
After queueing a hand inpainting workflow, the minimal UI now saves the latest hand reference prompt ID to `project_output/metadata/latest_hand_reference_prompt.json`.
After queueing hand reference generation, the minimal UI now explains that ComfyUI is generating, the prompt ID was saved for history checking, and the user should press Load hand refs after ComfyUI finishes.
If hand reference images are not available during manual loading, the UI now explains that generation may still be running and the user can wait and press Load hand refs again.
Missing, empty, or invalid hand reference output folders are now handled with simple status messages instead of crashing the UI.
The minimal UI can now export a simple hand reference sheet and show the saved sheet path after export.
The minimal UI now reopens the configured project output on startup, reloads saved prediction and hand reference thumbnails, and restores the saved selected candidate preview when possible.
It also has a simple `Reopen project` button for reloading the current `Project output` folder after changing that path.
The minimal UI now shows a compact project summary with the current output folder, prediction count, selected candidate status, mask status, hand reference count, and exported sheet count.
The minimal UI now has a `Check workflows` button that locally validates required workflow placeholders without connecting to ComfyUI.
The workflow check now also warns when the prediction color rough image placeholder is on a node that does not appear to be connected to the rest of the ComfyUI API workflow.
The workflow check now also warns when the hand inpainting selected candidate image or hand mask image placeholder is on a node that does not appear to be connected to the hand inpainting workflow.
Workflow mismatch warnings now explain that ComfyUI may accept the prompt even when disconnected image input nodes are ignored, and tell the user to reconnect nodes and export the API workflow again.
Workflow mismatch warnings now also explain that the placeholder may be on an isolated Load Image node and that the image or mask node must be connected to the actual KSampler, img2img, ControlNet, or inpainting route.
ComfyUI workflow requirements are now documented in `docs/COMFYUI_WORKFLOW_REQUIREMENTS.md`, including required placeholders and expected output folders.
The prediction workflow requirements now document the minimum recommended img2img route and a ControlNet-style route so the color rough image is actually used by generation.
Local AI setup guidance is now documented in `docs/LOCAL_AI_SETUP_GUIDE.md`.
The local AI setup guide now explains what to do when the app warns that the color rough image node is not connected.
The local AI setup guide now includes a beginner-friendly troubleshooting checklist for ComfyUI startup, endpoint checks, workflow JSON, model placement, saved selected candidates, saved masks, and manual output loading.
The post-AI setup implementation plan is now documented in `docs/ROADMAP.md` and `docs/TASK_QUEUE.md`.

Minimal color rough image selection handling now exists in `src/color_rough_ref_tool/core/color_rough_input.py`.
It records a user-selected existing file path as the current color rough.
The same module can now build minimal preview metadata for the selected input image, including file name, absolute path, file URI, and file size.
It can also copy the selected color rough into the project output input folder as `input/color_rough.<extension>`.
It validates supported color rough image extensions: `png`, `jpg`, `jpeg`, and `webp`.

The app can queue workflows to an external ComfyUI endpoint when ComfyUI is running and the workflow JSON is valid.
It still does not wait for generation completion or automatically copy ComfyUI outputs into the project folders.
After the latest manual workflow fixes, prediction generation and hand reference generation have both been reported working by the user.
Generated ComfyUI images may still need to be copied manually from the external ComfyUI output folder into `project_output/predictions/` or `project_output/hand_refs/` before pressing Load predictions or Load hand refs.

---

## Phase 12.1 Validation Attempt

Date: 2026-05-13

Goal:
Run one complete manual prediction test from one color rough image through external ComfyUI.

Result:
The test was started but did not pass as a valid color-rough-to-prediction test.

What was confirmed:

- External ComfyUI was reachable at `http://127.0.0.1:8188`.
- ComfyUI `/system_stats` returned HTTP 200.
- `workflows/prediction_workflow.json` exists.
- The prediction workflow contains the required color rough placeholder.
- Existing prediction output images are present in `project_output/predictions/`.

Problem found:

- `project_output/input/` did not contain a saved color rough image for the validation run.
- The current prediction workflow has `{{COLOR_ROUGH_IMAGE_PATH}}` on a `LoadImage` node, but that node is not connected to the generation flow.
- The workflow validation reported: `ComfyUI may accept the prompt, but the color rough image may be ignored because its node is not connected to the generation flow (node id: 8)`.
- Because of this, queueing the current workflow would not prove that prediction generation uses the selected color rough.

Decision:
Do not mark Phase 12.1 as complete yet. Fix or re-export the prediction workflow so the color rough image is connected to the actual img2img or ControlNet route, then run Phase 12.1 again with a saved color rough image.

Additional check:
An automated test command was attempted for workflow/prediction modules, but it failed in the local temp test folder with Windows `PermissionError` on `C:\RuougRef2\tmp\tests`. This was not a product-code failure.

---

## Phase 12 Validation Update

Date: 2026-05-13

What changed after the first failed prediction validation:

- `workflows/prediction_workflow.json` was fixed so `{{COLOR_ROUGH_IMAGE_PATH}}` is present and connected to the img2img generation route.
- `workflows/hand_inpainting_workflow.json` was fixed so `{{SELECTED_CANDIDATE_IMAGE_PATH}}` and `{{HAND_MASK_IMAGE_PATH}}` are present and connected to the inpainting route.
- The user reported that prediction generation worked after the prediction workflow fix.
- The user reported that hand reference generation worked after the hand workflow fix.

Remaining manual step:

- Finished ComfyUI images may still need to be copied manually into the app project folders before pressing Load predictions or Load hand refs.

Next usability plan:

- Add a manual output pickup flow where Load predictions and Load hand refs use the latest saved prompt ID to import finished images from ComfyUI history before refreshing thumbnails.
- Keep automatic polling for later. The next improvement should remain a user-triggered Load action.

---

## Phase 12.3 Sheet and Metadata Check

Date: 2026-05-13

Goal:
Confirm that saved results from the full workflow can produce a hand reference sheet and the basic project metadata files.

Result:
Passed.

What was confirmed:

- `project_output/predictions/` contains 2 prediction images.
- `project_output/selected/` contains the saved selected candidate `ComfyUI_00002_.png`.
- `project_output/masks/` contains the matching saved mask `ComfyUI_00002__hand_mask.png`.
- `project_output/hand_refs/` contains 4 hand reference images.
- `project_output/sheets/hand_sheet_001.png` was exported successfully.
- `project_output/metadata/project.json` was saved.
- `project_output/metadata/predictions.json` was saved.
- `project_output/metadata/hand_refs.json` was saved.
- `project_output/metadata/settings_snapshot.json` was saved.
- Existing latest prompt ID metadata files are still present for prediction and hand reference history checks.

Remaining note:
The app can create the needed sheet and metadata from saved local files, but output pickup from ComfyUI is still a manual load/import usability area planned for Phase 13.

---

## Phase 12.4 Final v0.1 Usage Notes

Date: 2026-05-13

Goal:
Document the final v0.1 usage flow and known issues after real local ComfyUI validation.

Result:
Completed.

What was updated:

- `docs/LOCAL_AI_SETUP_GUIDE.md` now includes a full v0.1 usage order from starting ComfyUI through exporting a hand reference sheet.
- The guide now lists the main saved output locations under `project_output/`.
- The guide now has a v0.1 known issues section for ComfyUI startup, external models, workflow JSON setup, manual loading, and quality limitations.
- The next development order now starts with Phase 13 output pickup usability.

Decision:
Phase 12 validation is complete enough for v0.1 documentation. The next work should improve manual output pickup without adding paid APIs, cloud GPU dependencies, bundled models, or automatic polling yet.

---

## Phase 13 Plan

Goal:
Make generated output pickup easier without adding cloud services, paid APIs, bundled models, or an automatic waiting loop.

Planned order:

1. Make Load predictions import finished images from the latest saved prediction prompt ID, then refresh thumbnails.
2. Make Load hand refs import finished images from the latest saved hand reference prompt ID, then refresh thumbnails.
3. Add simple messages for pending generation, copied images, missing ComfyUI output files, and history lookup failures.
4. Consider optional automatic polling only after the manual Load import flow is stable.

---

## Phase 13.1 Prediction Output Pickup

Date: 2026-05-13

Goal:
Make `Load predictions` import finished prediction images from the latest saved prediction prompt ID, then refresh the thumbnails.

Result:
Completed.

What changed:

- The prediction integration can now download completed prediction images reported by ComfyUI history through the existing ComfyUI endpoint's image view route.
- `Load predictions` now checks `project_output/metadata/latest_prediction_prompt.json` once when pressed.
- If the latest prediction prompt is complete, reported images are saved into `project_output/predictions/`.
- After the import attempt, the UI refreshes prediction thumbnails from `project_output/predictions/`.
- If no latest prediction prompt ID exists, `Load predictions` still behaves like a normal local folder refresh.
- If ComfyUI history says the prompt is still running, the status message tells the user to wait and press `Load predictions` again.

Scope notes:

- No automatic wait loop was added.
- No cloud/API integration was added.
- No ComfyUI, model, or checkpoint files were bundled.
- This is still a user-triggered manual Load action.

Verification:

- `python -m unittest tests.test_ui_app tests.test_comfyui_prediction`

---

## Phase 13.2 Hand Reference Output Pickup

Date: 2026-05-13

Goal:
Make `Load hand refs` import finished hand reference images from the latest saved hand reference prompt ID, then refresh the thumbnails.

Result:
Completed.

What changed:

- The hand inpainting integration can now download completed hand reference images reported by ComfyUI history through the existing ComfyUI endpoint's image view route.
- `Load hand refs` now checks `project_output/metadata/latest_hand_reference_prompt.json` once when pressed.
- If the latest hand reference prompt is complete, reported images are saved into `project_output/hand_refs/`.
- After the import attempt, the UI refreshes hand reference thumbnails from `project_output/hand_refs/`.
- If no latest hand reference prompt ID exists, `Load hand refs` still behaves like a normal local folder refresh.
- If ComfyUI history says the prompt is still running, the status message tells the user to wait and press `Load hand refs` again.

Scope notes:

- No automatic wait loop was added.
- No cloud/API integration was added.
- No ComfyUI, model, or checkpoint files were bundled.
- This is still a user-triggered manual Load action.

Verification:

- `python -m unittest tests.test_ui_app tests.test_comfyui_hand_inpainting`

---

## Phase 13.3 Output Pickup Messages

Date: 2026-05-13

Goal:
Improve the simple UI messages for pending generation, copied images, missing ComfyUI output files, and history lookup failures.

Result:
Completed.

What changed:

- `Load predictions` now explains when no saved prediction prompt ID exists and only the local predictions folder was refreshed.
- `Load predictions` now describes pending ComfyUI history as still generating or not ready yet.
- `Load predictions` now says when images were imported into `project_output/predictions/`.
- `Load predictions` now explains when ComfyUI history is complete but no prediction image files were listed.
- `Load hand refs` now explains when no saved hand reference prompt ID exists and only the local hand_refs folder was refreshed.
- `Load hand refs` now describes pending ComfyUI history as still generating or not ready yet.
- `Load hand refs` now says when images were imported into `project_output/hand_refs/`.
- `Load hand refs` now explains when ComfyUI history is complete but no hand reference image files were listed.
- Error messages now include clearer hints when history lookup fails or when ComfyUI history lists an image but the app cannot download it.

Scope notes:

- No automatic wait loop was added.
- No new ComfyUI connection method was added.
- No cloud/API integration was added.
- No ComfyUI, model, or checkpoint files were bundled.

Verification:

- `python -m unittest tests.test_ui_app tests.test_comfyui_hand_inpainting`

---

## Phase 13.4 Automatic Polling Decision

Date: 2026-05-13

Goal:
Consider whether automatic polling should be added now that the manual Load import flow is available.

Decision:
Do not add automatic polling for v0.1.

Reason:

- The manual `Load predictions` and `Load hand refs` flow is now understandable and stable enough as the default.
- Automatic polling would add background ComfyUI requests that are harder for beginners to see and reason about.
- Different ComfyUI workflows can take very different amounts of time and can save outputs in slightly different ways.
- A user-triggered Load action makes recovery simpler when ComfyUI is still generating, has failed, or reports no output images.

Future rule:
If automatic polling is added later, it should be opt-in, visible in the UI, stoppable, limited to the latest saved prompt ID, and backed by the manual Load buttons as a fallback.

What changed:

- `docs/ROADMAP.md` now records the Phase 13.4 decision and adds a future optional polling evaluation phase.
- `docs/LOCAL_AI_SETUP_GUIDE.md` now explains that automatic polling is intentionally deferred and that manual Load remains the stable v0.1 flow.
- No code changes were made.

Verification:

- Documentation-only change. Automated tests were not run.

---

## Phase 14.1 Optional Polling Re-evaluation

Date: 2026-05-13

Goal:
Revisit whether automatic polling should be implemented after the manual Load import flow became stable.

Decision:
Do not implement automatic polling yet.

Reason:

- The current manual `Load predictions` and `Load hand refs` flow is simple and visible.
- The app already explains pending generation, successful imports, missing output images, and history lookup failures.
- Automatic polling would add background behavior before there is enough real-use evidence that it solves a frequent problem.
- The next useful step is to run the app through real drawing-support sessions and record where the user hesitates.

Minimum future polling specification:

- Off by default.
- Opt-in from a visible UI control.
- Checks only the latest saved prompt ID.
- Stops after images are imported, after a short timeout, when ComfyUI is unreachable, when another generation starts, or when the user stops it.
- Manual `Load predictions` and `Load hand refs` remain available as the reliable fallback.

What changed:

- `docs/ROADMAP.md` now records the Phase 14.1 evaluation and a minimal future polling specification.
- `docs/LOCAL_AI_SETUP_GUIDE.md` now notes that polling is still not recommended for the current version.
- `docs/TASK_QUEUE.md` now moves the next work to real-use stabilization.
- No code changes were made.

Verification:

- Documentation-only change. Automated tests were not run.

---

## What Should Exist in v0.1

- Color rough loading
- ComfyUI settings
- Prediction generation trigger
- Prediction candidate viewing
- Candidate selection
- Manual hand mask editing
- Hand reference generation trigger
- Result saving
- Sheet export
- Metadata saving

---

## What Is Explicitly Out of Scope

- Local reference search
- Blender / 3D
- Automatic hand detection
- Custom AI training
- Other body parts
- Cloud sharing
- Model bundling

---

## Last Completed Task

Phase 14.1:
Re-evaluated automatic polling and decided not to implement it yet; recorded the minimum future specification.

---

## Current Next Task

Phase 15.1:
Run one real end-to-end workflow and record practical friction points before adding new automation.

---

## Known Risks / Constraints

- Output quality depends heavily on the user's chosen models and workflows.
- SDXL can be heavy on weaker GPUs.
- Manual masking is intentionally used to avoid adding model-training complexity.
- ComfyUI setup remains a user-side responsibility.
- ComfyUI `Load Image` nodes may need files in ComfyUI's expected input location, depending on the workflow. If a workflow uses absolute paths incorrectly, queueing may succeed while generation still does not use the image as intended.
- The current workflow test can prove that a placeholder exists and can catch clearly unconnected placeholder nodes, but it still cannot fully prove final image quality or whether the workflow uses the input effectively.

---

## Notes

The software should remain a workflow support tool, not a full image-generation platform.

The development focus is:
- simplicity
- directness
- local no-cost generation workflow
- minimal scope
