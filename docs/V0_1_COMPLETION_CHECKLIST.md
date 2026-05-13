# v0.1 Completion Checklist

This checklist is for deciding whether the current app is ready to call itself v0.1.

The app must remain a local workflow support tool. It must not include ComfyUI, AI models, paid APIs, cloud GPU settings, local reference search, Blender, or 3D features.

---

## 1. v0.1 Scope

v0.1 is complete when the user can run this flow with external local ComfyUI:

```text
color rough
-> prediction generation
-> choose one prediction candidate
-> save selected candidate
-> draw and save hand mask
-> hand reference generation
-> load hand reference images
-> export a simple sheet
```

The flow may use manual Load buttons after ComfyUI finishes. Automatic polling is not required for v0.1.

---

## 2. Before the End-to-End Check

Confirm these items first:

- External ComfyUI starts outside this app.
- `http://127.0.0.1:8188` opens in a browser.
- Local models are installed only in ComfyUI's model folders.
- Real API-format workflow JSON files are available:
  - `workflows/prediction_workflow.json`
  - `workflows/hand_inpainting_workflow.json`
- The prediction workflow uses the color rough image in the actual generation route.
- The hand inpainting workflow uses both:
  - selected candidate image
  - saved mask image
- The app launches from `run_app.py` or `start_app.bat`.

---

## 3. End-to-End Confirmation Steps

Use one real color rough image and follow this order.

```text
1. Start external ComfyUI.
2. Open http://127.0.0.1:8188 in a browser and confirm ComfyUI is ready.
3. Start Color Rough Reference Tool.
4. Press Choose image and select one color rough.
5. Confirm the ComfyUI endpoint is http://127.0.0.1:8188, unless ComfyUI uses another port.
6. Select the real prediction workflow JSON.
7. Select the real hand inpainting workflow JSON.
8. Press Check settings.
9. Press Check workflows.
10. Press Regenerate prediction.
11. Wait until ComfyUI finishes the prediction generation.
12. Press Load predictions.
13. Confirm prediction thumbnails appear.
14. Select one prediction candidate.
15. Press Save selected.
16. Press Load selected for mask.
17. Draw a hand mask with Brush or Rectangle.
18. Press Save mask.
19. Press Regenerate hand ref.
20. Wait until ComfyUI finishes the hand reference generation.
21. Press Load hand refs.
22. Confirm hand reference thumbnails appear.
23. Press Export sheet.
24. Confirm the sheet image is saved.
25. Confirm project metadata exists.
```

---

## 4. Files and Folders to Confirm

After the check, these folders should contain the expected files:

```text
project_output/input/
project_output/predictions/
project_output/selected/
project_output/masks/
project_output/hand_refs/
project_output/sheets/
project_output/metadata/
```

Minimum metadata files:

```text
project_output/metadata/project.json
project_output/metadata/predictions.json
project_output/metadata/hand_refs.json
project_output/metadata/settings_snapshot.json
```

Prompt ID metadata may also exist:

```text
project_output/metadata/latest_prediction_prompt.json
project_output/metadata/latest_hand_reference_prompt.json
```

---

## 5. Practical Friction Notes

During the end-to-end check, write down any point where the user hesitates.

Use these questions:

- Was it clear when to start ComfyUI?
- Was the endpoint easy to understand?
- Was it clear which workflow JSON files to choose?
- Did `Check workflows` explain problems well enough?
- Was it clear that generation happens in external ComfyUI?
- Was it clear when to press `Load predictions`?
- Was candidate selection easy to understand?
- Was it clear that `Save selected` must happen before mask editing?
- Was mask drawing good enough for simple hand areas?
- Was it clear that `Save mask` must happen before `Regenerate hand ref`?
- Was it clear when to press `Load hand refs`?
- Was sheet export easy to confirm?
- Were error messages understandable without code knowledge?

Record each issue like this:

```text
Issue:
Where it happened:
What the user expected:
What the app showed:
Blocking for v0.1: yes / no
Suggested fix:
```

---

## 6. v0.1 Completion Criteria

v0.1 can be marked complete if all must-pass items below are true.

Must pass:

- The app launches without requiring a terminal-only workflow.
- A color rough image can be selected and saved into the project output.
- Settings and workflow paths can be checked.
- Prediction generation can be queued to external ComfyUI.
- Finished prediction images can be loaded into the app.
- One prediction candidate can be selected and saved.
- The saved candidate can be opened for mask editing.
- A simple brush or rectangle mask can be saved.
- Hand reference generation can be queued to external ComfyUI.
- Finished hand reference images can be loaded into the app.
- A simple hand reference sheet can be exported.
- Basic metadata is saved.
- Known limitations are documented.
- The app still does not bundle models, ComfyUI, paid APIs, cloud GPU settings, local search, Blender, or 3D features.

Acceptable for v0.1:

- Manual `Load predictions` and `Load hand refs` are still required.
- Workflow quality depends on the user's ComfyUI setup.
- The UI is simple and utilitarian.
- Mask editing is basic.
- The docs are used for setup guidance.

Not acceptable for v0.1:

- The app cannot complete the full color rough to hand reference flow at all.
- The app appears to require paid APIs or cloud GPU services.
- Model files are placed inside this app.
- A beginner cannot recover from common setup mistakes using the current messages and docs.

---

## 7. v0.1 Decision Log Template

Use this template after the real check:

```text
Date:
Tester:
ComfyUI endpoint:
Prediction workflow:
Hand inpainting workflow:
Model family:

Result:
pass / pass with minor issues / blocked

What worked:

What confused the user:

Blocking issues before v0.1:

Non-blocking issues for later:

Decision:
v0.1 complete / needs one more fix pass
```
