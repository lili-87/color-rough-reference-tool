# ComfyUI Workflow Requirements

This document describes the minimum workflow rules needed for this app to call external ComfyUI.

The app does not include ComfyUI, AI models, checkpoints, paid APIs, or cloud GPU settings.
ComfyUI and all models are installed and managed separately by the user.

---

## 1. Workflow Files

The app expects two user-provided ComfyUI workflow JSON files:

```text
workflows/prediction_workflow.json
workflows/hand_inpainting_workflow.json
```

The files currently in `workflows/` are placeholders.
They must be replaced with real ComfyUI workflow JSON files before real generation can work.

---

## 2. Prediction Workflow

Purpose:

```text
color rough image
↓
completion prediction images
```

The prediction workflow must contain one of these placeholder strings where the color rough image path should be inserted:

```text
{{COLOR_ROUGH_IMAGE_PATH}}
{{COLOR_ROUGH_IMAGE}}
```

When the app queues prediction generation, it replaces those strings with the selected color rough image path.

Expected output location:

```text
project_output/predictions/
```

Supported output image formats:

```text
png / jpg / jpeg / webp
```

---

## 3. Hand Inpainting Workflow

Purpose:

```text
selected prediction candidate
+ hand mask image
↓
hand reference images
```

The hand inpainting workflow must contain one placeholder for the selected prediction image:

```text
{{SELECTED_CANDIDATE_IMAGE_PATH}}
{{SELECTED_CANDIDATE_IMAGE}}
```

It must also contain one placeholder for the saved hand mask image:

```text
{{HAND_MASK_IMAGE_PATH}}
{{HAND_MASK_IMAGE}}
```

When the app queues hand reference generation, it replaces those strings with the saved selected candidate path and saved mask path.

Expected output location:

```text
project_output/hand_refs/
```

Supported output image formats:

```text
png / jpg / jpeg / webp
```

---

## 4. What Is Not Implemented Yet

The app can queue workflows and read output folders, but it does not yet:

- wait for ComfyUI generation to finish
- automatically fetch images from ComfyUI history
- create ComfyUI workflows by itself
- install ComfyUI
- install or bundle AI models
- use paid APIs or cloud GPU services

For now, generated files must appear in the expected project output folders before the app can show them.

---

## 5. When To Install Generation AI

Install ComfyUI and local models after the real workflow files are ready to be tested.

The intended order is:

```text
1. Prepare real ComfyUI workflows.
2. Confirm the placeholders above are inside those workflows.
3. Install ComfyUI externally.
4. Place local models in the user's ComfyUI model folders.
5. Start ComfyUI locally.
6. Use this app to queue workflows and manage outputs.
```

Use local no-cost models only for the initial version.
