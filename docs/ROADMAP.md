# Color Rough Reference Tool - Roadmap

## Phase 0: Project Foundation

Goal:
Prepare the project structure and settings for a standalone app.

Tasks:
- Create project skeleton
- Define output folder structure
- Define settings storage
- Prepare docs and workflow placeholders

Completion condition:
The app can store settings and prepare project output directories.

---

## Phase 1: Color Rough Input

Goal:
Load and manage the input color rough.

Tasks:
- Add image loading for color rough
- Support png / jpg / jpeg / webp
- Show input preview
- Save input image into project output folder

Completion condition:
The user can load and preview a color rough.

---

## Phase 2: ComfyUI Configuration

Goal:
Connect the software to external ComfyUI.

Tasks:
- Add settings for ComfyUI path or endpoint
- Add settings for workflow file locations
- Add connection / execution test
- Save settings snapshot

Completion condition:
The app can validate ComfyUI configuration.

---

## Phase 3: Prediction Generation

Goal:
Generate multiple completion-prediction images from the color rough.

Tasks:
- Trigger external ComfyUI workflow for prediction generation
- Pass the color rough input to the workflow
- Wait for generation output
- Read prediction images from output folder
- Show prediction candidates in the UI

Completion condition:
The user can generate and view multiple prediction candidates.

---

## Phase 4: Candidate Selection

Goal:
Let the user choose the best prediction candidate.

Tasks:
- Add candidate selection UI
- Allow selecting one prediction image
- Save selected candidate into `selected/`
- Record selected candidate in metadata

Completion condition:
The user can choose one prediction candidate for the next step.

---

## Phase 5: Hand Mask Editing

Goal:
Let the user specify the hand area manually.

Tasks:
- Show selected prediction image
- Add simple mask editing UI
- Support brush or rectangle-based masking
- Save mask image into `masks/`

Completion condition:
The user can create and save a hand mask for the selected image.

---

## Phase 6: Hand Reference Generation

Goal:
Generate hand reference images using the selected prediction and hand mask.

Tasks:
- Trigger external ComfyUI hand inpainting workflow
- Pass selected image and mask
- Read generated hand reference outputs
- Show hand reference results

Completion condition:
The user can generate and view multiple hand reference images.

---

## Phase 7: Save and Export

Goal:
Save project results and create sheet output.

Tasks:
- Save metadata
- Save selected prediction
- Save hand references
- Export simple hand reference sheet image

Completion condition:
The user can preserve the project results as usable reference assets.

---

## Phase 8: Usability Improvements

Goal:
Improve daily usability without changing the core scope.

Tasks:
- Better thumbnail display
- Regenerate buttons
- Clear project summary
- Better error messages
- Session restore if useful

Completion condition:
The workflow is smoother, while staying simple and focused.

---

## Phase 9: Real Local AI Workflow Check

Goal:
Confirm that the external ComfyUI workflows are real production workflows, not only queue tests.

Tasks:
- Verify that the prediction workflow actually uses the color rough image
- Prefer img2img or ControlNet-style structure for prediction generation
- Verify that the hand inpainting workflow actually uses both selected candidate and mask image
- Keep workflow files in API-format JSON
- Keep all models inside the user's external ComfyUI installation

Completion condition:
The app can queue workflows that use the provided image inputs in ComfyUI.

---

## Phase 10: Generation Completion and Output Pickup

Goal:
Reduce manual file handling after pressing regenerate buttons.

Tasks:
- Store the prompt ID returned by ComfyUI
- Check ComfyUI history for that prompt ID
- Detect when generation has finished
- Find generated image file names from ComfyUI history
- Copy prediction outputs into `project_output/predictions/`
- Copy hand reference outputs into `project_output/hand_refs/`
- Refresh the UI after files are copied

Completion condition:
The user can press regenerate, wait, and see generated images appear in the app without manually copying files.

---

## Phase 11: Beginner-Friendly Generation Flow

Goal:
Make the local AI workflow easier to use and easier to recover from when something is missing.

Tasks:
- Show clearer status while generation is queued or waiting
- Explain when ComfyUI is not running
- Explain when workflow placeholders are missing
- Explain when ComfyUI generated files but the app could not copy them
- Prevent hand reference generation when selected candidate or mask is missing
- Keep the UI simple and avoid advanced ComfyUI controls inside this app

Completion condition:
The user can follow the full workflow with simple messages and minimal manual checking.

---

## Phase 12: v0.1 Validation

Goal:
Confirm the first practical version works from start to finish.

Tasks:
- Test with one real color rough image
- Generate prediction candidates through external ComfyUI
- Select one candidate
- Draw and save a hand mask
- Generate hand reference images through external ComfyUI
- Export a hand reference sheet
- Confirm metadata files are saved
- Update user-facing setup notes based on real test results

Completion condition:
The full color rough to hand reference workflow works locally with external ComfyUI and user-provided models.

---

## Phase 13: Output Pickup Usability

Goal:
Reduce the remaining manual copying after ComfyUI finishes generation.

Tasks:
- Make Load predictions try to import finished images from the latest saved prediction prompt ID before refreshing thumbnails
- Make Load hand refs try to import finished images from the latest saved hand reference prompt ID before refreshing thumbnails
- Show a simple message when generation is still running, when images were copied, or when ComfyUI history cannot find output files
- Keep this as a manual Load button action first
- Do not add automatic polling until the manual import flow is stable

Completion condition:
After ComfyUI finishes generation, the user can press Load predictions or Load hand refs and the app copies the finished images into the project output folders automatically.

Phase 13.4 decision:
The manual Load import flow is stable enough for v0.1, but automatic polling is deferred.
Keep the user-triggered Load flow as the default because it is easier to understand, avoids background requests to ComfyUI, and is safer while workflow output behavior still varies.
If polling is added later, it should be opt-in, visibly stoppable, and limited to checking the latest saved prompt ID for a short time after the user presses Regenerate.

---

## Phase 14: Optional Polling Evaluation

Goal:
Consider a small opt-in helper that checks ComfyUI history for a short time after generation is queued.

Phase 14.1 evaluation:
Do not implement automatic polling yet.
The current manual Load flow is clear, recoverable, and safer for the first local version.
Polling should only be revisited after repeated real use shows that pressing Load manually is a frequent source of mistakes or frustration.

Possible tasks:
- Add a visible "Check automatically after regenerate" option, disabled by default
- Poll only the latest saved prompt ID
- Stop polling after images are imported, after a timeout, or when the user starts a different action
- Keep manual Load buttons available as the reliable fallback

Minimum future specification:
- Default: off
- Scope: latest saved prompt ID only
- Interval: slow enough to avoid noisy background requests, for example every few seconds
- Stop conditions: image import succeeds, user presses another generation button, user closes the app, ComfyUI becomes unreachable, or a short timeout is reached
- UI requirement: show that automatic checking is active and let the user stop it
- Fallback: manual Load predictions and Load hand refs must always remain available

Completion condition:
Automatic polling, if added, remains a small convenience layer and does not replace the manual Load workflow.

---

## Phase 15: v0.1 Real Use Stabilization

Goal:
Use the app in a small number of real drawing-support sessions and record practical friction points before adding new automation.

Tasks:
- Run one real end-to-end workflow and record where the user hesitates
- Check whether manual Load is acceptable in practice
- Check whether workflow setup guidance is understandable without Codex help
- Prioritize only fixes that reduce confusion in the existing local workflow

Completion condition:
The next improvements are based on real usage friction, not speculation.

---

## Not Planned for Initial Version

- Local reference search
- Blender / 3D integration
- Automatic hand detection
- Custom AI model training
- Multi-part body reference generation
- Cloud execution
- Paid API usage
