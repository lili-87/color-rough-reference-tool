# Local AI Setup Guide

This guide explains when and how to add generation AI for this app.

The app itself does not include ComfyUI, AI models, checkpoints, paid APIs, or cloud GPU settings.
Use externally installed ComfyUI and local no-cost models only.

---

## 1. Before Installing AI

Confirm these app-side items first:

```text
1. The app launches.
2. Color rough image selection works.
3. Project output folders are created.
4. Prediction and hand workflow file paths are set.
5. Check workflows passes after real workflow JSON files are selected.
```

The placeholder workflow files in `workflows/` are not enough for real generation.
They must be replaced with real ComfyUI workflow JSON files.

---

## 2. Install ComfyUI Externally

Install ComfyUI outside this app.

Recommended beginner path:

```text
1. Install Python supported by ComfyUI.
2. Install Git.
3. Download or clone ComfyUI from its official repository.
4. Install ComfyUI dependencies by following the official ComfyUI instructions.
5. Start ComfyUI locally.
6. Open the ComfyUI browser page and confirm it runs.
```

The usual local endpoint is:

```text
http://127.0.0.1:8188
```

Use that value in the app's `ComfyUI endpoint` field unless your ComfyUI uses a different port.

---

## 3. Prepare Local Models

Use models that you have the right to use locally.

Initial target:

```text
SDXL anime-style checkpoint
ControlNet or img2img-compatible setup for prediction
SDXL inpainting-compatible setup for hand reference generation
```

Place the models in the correct ComfyUI model folders according to ComfyUI's instructions.

Do not place model files inside this app repository.
Do not commit or redistribute model files with this app.

---

## 4. Prepare Real Workflows

Create or edit two ComfyUI workflows:

```text
prediction workflow
hand inpainting workflow
```

The prediction workflow must contain one of:

```text
{{COLOR_ROUGH_IMAGE_PATH}}
{{COLOR_ROUGH_IMAGE}}
```

The hand inpainting workflow must contain one selected-candidate placeholder:

```text
{{SELECTED_CANDIDATE_IMAGE_PATH}}
{{SELECTED_CANDIDATE_IMAGE}}
```

It must also contain one hand-mask placeholder:

```text
{{HAND_MASK_IMAGE_PATH}}
{{HAND_MASK_IMAGE}}
```

Save the exported workflow JSON files and select them in the app.
Then press `Check workflows`.

For the prediction workflow, the color rough image must be connected into the actual generation route.
If `Check workflows` says the color rough image node may not be connected, the workflow probably has a `Load Image` node sitting by itself.

Beginner-friendly img2img route:

```text
1. Add or use a Load Image node.
2. Put {{COLOR_ROUGH_IMAGE_PATH}} in that Load Image node's image value after exporting API JSON.
3. Connect Load Image to VAE Encode.
4. Connect VAE Encode to KSampler latent_image.
5. Connect KSampler to VAE Decode.
6. Connect VAE Decode to Save Image.
7. Export the workflow in API format again.
8. Save it as workflows/prediction_workflow.json.
9. Press Check workflows in this app.
```

Suggested first denoise value:

```text
0.55
```

If the result follows the rough too strongly, raise denoise a little.
If the result ignores the rough, lower denoise or use ControlNet.

ControlNet route:

```text
Load Image with {{COLOR_ROUGH_IMAGE_PATH}}
↓
ControlNet-related nodes
↓
KSampler conditioning
```

ControlNet is useful later, but it requires extra models and sometimes extra ComfyUI nodes.
Do not put those models inside this app folder.

---

## 5. Expected Output Folders

For the current version, generated images should appear in these folders:

```text
project_output/predictions/
project_output/hand_refs/
```

The app can read and show images from those folders.
It does not yet wait for ComfyUI generation completion or fetch ComfyUI history automatically.

Supported image formats:

```text
png / jpg / jpeg / webp
```

---

## 6. First Real Generation Test

After ComfyUI and models are ready:

```text
1. Start ComfyUI.
2. Start this app.
3. Choose a color rough image.
4. Set the real prediction workflow file.
5. Set the real hand inpainting workflow file.
6. Press Check settings.
7. Press Check workflows.
8. Press Regenerate prediction.
9. Wait in ComfyUI until generation finishes.
10. Put or configure prediction outputs into project_output/predictions/.
11. Press Reopen project or Load predictions.
```

Hand reference testing comes after selecting and saving a prediction candidate and saving a hand mask.

---

## 7. Still Not Implemented

These are intentionally left for later app-side tasks:

- waiting for ComfyUI generation to finish
- reading ComfyUI history automatically
- copying ComfyUI output images automatically
- verifying that the workflow graph actually uses the provided image inputs
- advanced workflow editing
- cloud GPU support
- paid API support
- bundled model installation

---

## 8. Current Next Development Order

After the first successful queue test, continue in this order:

```text
1. Confirm the prediction workflow really uses the color rough image.
2. Confirm the hand inpainting workflow really uses selected candidate + mask.
3. Add ComfyUI history lookup for queued prompt IDs.
4. Copy finished prediction images automatically into project_output/predictions/.
5. Copy finished hand reference images automatically into project_output/hand_refs/.
6. Refresh thumbnails automatically after copied outputs are available.
7. Run one complete v0.1 test from color rough to exported hand sheet.
```

Do not add paid APIs, cloud GPU settings, bundled models, local reference search, or Blender / 3D work during this initial version.
