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

## Not Planned for Initial Version

- Local reference search
- Blender / 3D integration
- Automatic hand detection
- Custom AI model training
- Multi-part body reference generation
- Cloud execution
- Paid API usage
