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
The app does not yet wait for ComfyUI generation completion automatically.
If the Load buttons do not show new images, copy the generated files from the external ComfyUI output folder into the matching project output folder, then press Load predictions or Load hand refs.

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

## 7. v0.1 Full Usage Steps

Use this order for the current v0.1 workflow.

```text
1. Start external ComfyUI.
2. Confirm http://127.0.0.1:8188 opens in a browser.
3. Start Color Rough Reference Tool.
4. Choose a color rough image.
5. Confirm the ComfyUI endpoint is correct.
6. Select the prediction workflow JSON.
7. Select the hand inpainting workflow JSON.
8. Press Check settings.
9. Press Check workflows.
10. Press Regenerate prediction.
11. Wait until ComfyUI finishes generation.
12. Press Load predictions.
13. Select one prediction candidate.
14. Press Save selected.
15. Press Load selected for mask.
16. Draw a hand mask with Brush or Rectangle.
17. Press Save mask.
18. Press Regenerate hand ref.
19. Wait until ComfyUI finishes generation.
20. Press Load hand refs.
21. Press Export sheet if you want a sheet image.
22. Confirm saved files in project_output/.
```

Main saved locations:

```text
project_output/input/
project_output/predictions/
project_output/selected/
project_output/masks/
project_output/hand_refs/
project_output/sheets/
project_output/metadata/
```

The app is meant to organize and save local ComfyUI results.
ComfyUI, checkpoints, ControlNet models, inpainting models, and custom nodes stay outside this app.

---

## 8. v0.1 Known Issues

These are known limitations of the current v0.1 validation state.

- ComfyUI must be started separately before generation.
- The app does not include models, checkpoints, ComfyUI, paid APIs, or cloud GPU setup.
- Workflow JSON files must be real ComfyUI API-format workflows.
- `Check workflows` can catch missing placeholders and clearly disconnected placeholder nodes, but it cannot judge final image quality.
- A workflow can still produce poor results if denoise, prompt, checkpoint, VAE, mask, or inpainting settings are not suitable.
- If generated images do not appear after pressing Load predictions or Load hand refs, wait for ComfyUI to finish and press the Load button again.
- Depending on the workflow output path, generated images may still need to be copied or configured into `project_output/predictions/` or `project_output/hand_refs/`.
- Hand reference quality depends heavily on the selected candidate, mask shape, inpainting workflow, and model choice.
- Manual mask editing is intentionally simple. Automatic hand detection is not part of v0.1.
- Advanced project management, multiple named projects, and automatic background polling are not part of v0.1.
- Automatic polling was considered after the manual Load flow became available, but it is intentionally deferred. For now, press Load predictions or Load hand refs after ComfyUI finishes.

Recommended first working setup:

```text
SDXL anime checkpoint
simple img2img prediction workflow
simple inpainting workflow
manual mask
local ComfyUI only
```

After this works, improve quality by adjusting prompts, denoise, mask size, inpainting settings, or by adding ControlNet inside ComfyUI.

---

## 9. Troubleshooting Checklist

If generation does not work, check these items from top to bottom.

```text
1. Is ComfyUI running?
   The ComfyUI command window must stay open.

2. Does http://127.0.0.1:8188 open in a browser?
   If not, ComfyUI is not ready or the port is different.

3. Does the app's ComfyUI endpoint match the browser URL?
   The usual value is http://127.0.0.1:8188.

4. Did you select real API-format workflow JSON files?
   The placeholder files alone cannot generate images.

5. Does Check workflows pass?
   If it warns about disconnected image nodes, reconnect the Load Image or mask nodes in ComfyUI and export API JSON again.

6. Is a local SDXL checkpoint installed in ComfyUI's model folder?
   Keep model files inside the external ComfyUI installation, not inside this app folder.

7. For prediction, did you choose a color rough image before pressing Regenerate prediction?

8. For hand reference, did you Save selected and Save mask before pressing Regenerate hand ref?

9. If ComfyUI accepted the prompt but no image appears in the app, wait until ComfyUI finishes, then press Load predictions or Load hand refs.

10. If images still do not appear, check where ComfyUI saved them and copy or configure them into:
    project_output/predictions/
    project_output/hand_refs/
```

Keep the first working setup simple. Use one SDXL checkpoint first, then add ControlNet or inpainting-specific models only when the basic workflow is confirmed.

---

## 10. Still Not Implemented

These are intentionally left for later app-side tasks:

- automatic waiting for ComfyUI generation to finish
- fully automatic polling after generation
- a polished output pickup flow for every workflow shape
- proving final image quality or artistic correctness
- advanced workflow editing
- cloud GPU support
- paid API support
- bundled model installation

---

## 11. Current Next Development Order

After v0.1 validation and Phase 13 output pickup work:

```text
1. Keep the manual Load predictions / Load hand refs flow as the stable default.
2. Use more real projects to confirm workflow output behavior.
3. Consider optional polling later only if repeated manual Load presses become a real usability problem.
4. If polling is added later, make it opt-in, visible, stoppable, and limited to the latest saved prompt ID.
```

Phase 14.1 re-evaluation:
Automatic polling is still not recommended for the current version.
The next useful step is to use the app on a real drawing workflow and write down where the user gets stuck.
If the main repeated problem is "I forget to press Load after generation finishes," then optional polling can be reconsidered.

Do not add paid APIs, cloud GPU settings, bundled models, local reference search, or Blender / 3D work during this initial version.
