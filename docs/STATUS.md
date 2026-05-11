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

Implementation should begin by inspecting the current project structure and confirming the app foundation.

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

Documentation set prepared for the approved concept.

---

## Current Next Task

Phase 0.1:
Inspect the current project structure without changing code.

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
