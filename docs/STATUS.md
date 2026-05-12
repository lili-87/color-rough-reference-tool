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
Missing, empty, or invalid prediction output folders are now handled with simple status messages instead of crashing the UI.
The minimal UI can now select one loaded prediction candidate with a radio button and show the selected file name in the status area.
The minimal UI can now copy the selected prediction candidate into `project_output/selected` while keeping the original file name.
It now saves minimal selected-candidate metadata to `project_output/metadata/selected_candidate.json`.
The minimal UI can now load the saved selected candidate metadata and show the selected candidate in a simple mask editing preview area.
The mask editing preview now has a minimal brush tool for drawing red mask strokes on the displayed selected candidate.
The mask editing preview now also has a minimal rectangle tool for marking a rectangular mask area on the displayed selected candidate.
The minimal UI can now save the drawn brush and rectangle mask as a black-and-white PNG in `project_output/masks`.
UI error dialogs now add beginner-friendly hints before showing the original technical detail.
Minimal hand inpainting workflow triggering now exists in `src/color_rough_ref_tool/integrations/comfyui/hand_inpainting.py`.
It can load the configured hand inpainting workflow JSON and send it to an external ComfyUI `/prompt` endpoint.
It can now replace selected candidate and hand mask placeholders in the hand inpainting workflow before sending the prompt.
The supported hand workflow placeholder strings are `{{SELECTED_CANDIDATE_IMAGE_PATH}}`, `{{SELECTED_CANDIDATE_IMAGE}}`, `{{HAND_MASK_IMAGE_PATH}}`, and `{{HAND_MASK_IMAGE}}`.
It can now read generated hand reference image files from a hand reference output folder.
Supported hand reference output image formats are `png`, `jpg`, `jpeg`, and `webp`.
The minimal UI can now show hand reference images from `project_output/hand_refs` in a simple thumbnail area.
Images that Tkinter can preview are shown as small thumbnails; unsupported preview formats still appear by file name.
The minimal UI can now queue the hand inpainting workflow again from the saved selected candidate and saved hand mask.
Missing, empty, or invalid hand reference output folders are now handled with simple status messages instead of crashing the UI.
The minimal UI can now export a simple hand reference sheet and show the saved sheet path after export.
The minimal UI now reopens the configured project output on startup, reloads saved prediction and hand reference thumbnails, and restores the saved selected candidate preview when possible.
It also has a simple `Reopen project` button for reloading the current `Project output` folder after changing that path.

Minimal color rough image selection handling now exists in `src/color_rough_ref_tool/core/color_rough_input.py`.
It records a user-selected existing file path as the current color rough.
The same module can now build minimal preview metadata for the selected input image, including file name, absolute path, file URI, and file size.
It can also copy the selected color rough into the project output input folder as `input/color_rough.<extension>`.
It validates supported color rough image extensions: `png`, `jpg`, `jpeg`, and `webp`.

No live ComfyUI connection check or generation completion waiting exists yet.

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

Phase 8:
Added simple project reopen support for the configured project output.

---

## Current Next Task

Phase 8:
No unfinished task remains in `docs/TASK_QUEUE.md`.
Choose the next small task before implementation.

---

## Known Risks / Constraints

- Output quality depends heavily on the user's chosen models and workflows.
- SDXL can be heavy on weaker GPUs.
- Manual masking is intentionally used to avoid adding model-training complexity.
- ComfyUI setup remains a user-side responsibility.

---

## Notes

The software should remain a workflow support tool, not a full image-generation platform.

The development focus is:
- simplicity
- directness
- local no-cost generation workflow
- minimal scope
