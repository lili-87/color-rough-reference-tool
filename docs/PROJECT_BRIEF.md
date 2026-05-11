# Color Rough Reference Tool - Project Brief

## 1. Project Purpose

Color Rough Reference Tool is a standalone tool for illustrators.

Its purpose is to:

1. Accept a user-created color rough.
2. Generate multiple completion-prediction images from that color rough.
3. Let the user choose the best candidate.
4. Generate hand reference images based on the selected candidate.
5. Save the results as drawing reference material.

This tool is **not connected to LaughRef**.
It is designed as a separate standalone application.

---

## 2. Core Workflow

```text
Color rough
↓
Generate multiple completion-prediction images
↓
User selects one candidate
↓
User masks the hand area
↓
Generate hand reference images
↓
Save results and optional sheet
```

---

## 3. Main Design Principles

- Do not prioritize search-based workflows.
- Do not use Blender / 3D in the initial version.
- Do not include local reference search in the initial version.
- Focus on color rough → prediction → hand reference.
- Keep the application simple and direct.
- Do not bundle AI models with the software.
- Use **externally installed ComfyUI** as the generation backend.
- The user provides their own local models.
- The software only calls ComfyUI workflows and manages the results.

---

## 4. AI Strategy

The tool itself does not contain built-in generation models.

Instead, it uses:

- **ComfyUI** (externally installed by the user)
- **SDXL-based anime-style local model**
- **ControlNet / img2img** for prediction generation
- **SDXL Inpainting** for hand reference generation

Initial policy:

- Only **local models**
- Only **no-cost usage**
- No paid APIs
- No cloud dependency
- No model bundling

---

## 5. Scope of the Initial Version

### Included

- Load color rough image
- Configure ComfyUI path / connection and workflow files
- Generate multiple prediction images
- Show prediction candidates
- Allow selecting one candidate
- Provide hand mask editing
- Generate hand reference images
- Save project outputs
- Save optional hand reference sheet
- Save metadata

### Not Included

- Local reference search
- Blender integration
- 3D mannequin / scaffold
- Automatic hand detection
- Training custom AI models
- Other body part support
- Database management
- Cloud sharing
- Full replacement UI for ComfyUI

---

## 6. Output Structure

```text
project_output/
├ input/
│  └ color_rough.png
├ predictions/
│  ├ pred_001.png
│  ├ pred_002.png
│  ├ pred_003.png
│  └ pred_004.png
├ selected/
│  └ pred_002.png
├ masks/
│  └ pred_002_hand_mask.png
├ hand_refs/
│  ├ pred_002_hand_ref_001.png
│  ├ pred_002_hand_ref_002.png
│  └ pred_002_hand_ref_003.png
├ sheets/
│  └ hand_sheet_001.png
└ metadata/
   ├ project.json
   ├ predictions.json
   ├ hand_refs.json
   └ settings_snapshot.json
```

---

## 7. Success Condition for v0.1

The first practical version is successful if the user can:

1. Load a color rough.
2. Trigger ComfyUI to generate multiple prediction images.
3. View and select one candidate.
4. Create a hand mask for the selected candidate.
5. Trigger ComfyUI to generate multiple hand reference images.
6. Save results and optional sheet output.

---

## 8. Cost Policy

- AI-free development phase: almost no extra cost.
- Local AI usage phase: no API fee, no monthly fee if the user already has a capable GPU PC.
- ComfyUI is external.
- Models are external.
- This software does not redistribute models.

The initial design assumes:
- local execution
- no-cost model usage
- user-managed ComfyUI installation
