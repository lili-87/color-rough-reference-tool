# Color Rough Reference Tool - Development Rules

These rules define how implementation work should proceed.

## 1. Work Style

- Implement only one small task at a time.
- Do not make large architectural rewrites unless explicitly requested.
- Do not add unrelated features.
- Prefer simple, readable code.
- Keep the initial version narrow in scope.
- Explain implementation details in beginner-friendly language.

---

## 2. Required Reading Before Work

Before implementation, always read:

- `docs/PROJECT_BRIEF.md`
- `docs/DEVELOPMENT_RULES.md`
- `docs/ROADMAP.md`
- `docs/TASK_QUEUE.md`
- `docs/STATUS.md`

Then inspect the current project structure before making changes.

---

## 3. Before Changing Code

Before implementation:

1. Identify the next unfinished task in `TASK_QUEUE.md`.
2. Inspect the current codebase.
3. Identify which files will likely change.
4. Write a short work plan.
5. Keep the scope limited to the selected task.

---

## 4. During Implementation

- Keep changes minimal.
- Preserve existing behavior when possible.
- Avoid adding heavy dependencies unless necessary.
- Avoid introducing paid services.
- Do not assume cloud access.
- Keep ComfyUI integration isolated in clearly named modules.
- Do not bundle models into the app.

---

## 5. AI Integration Rules

The software should treat AI generation as external local processing.

Rules:

- ComfyUI is external.
- Models are external.
- The app should call workflows, not reimplement image generation.
- The app should focus on:
  - input handling
  - workflow triggering
  - result viewing
  - selection
  - masking
  - saving
  - metadata
  - sheet export

Initial version must use:

- local models only
- no paid API
- no automatic hand detection
- manual hand mask creation

---

## 6. After Implementation

After making changes, report:

1. Files changed
2. What was implemented
3. How to test it
4. Known issues
5. What should be done next

Then update:

- `docs/TASK_QUEUE.md`
- `docs/STATUS.md`

---

## 7. Testing Rules

Every task should include a clear manual test procedure.

Example:

```text
1. Launch the app.
2. Open settings.
3. Set ComfyUI path or connection.
4. Load a color rough image.
5. Run prediction generation.
6. Confirm candidate images appear.
```

If automated tests exist and are relevant, run them.
If testing cannot be done, explain why.

---

## 8. Git Rules

- Do not run destructive Git commands unless explicitly requested.
- Do not reset history or force-push.
- Prefer small commits.
- Use clear commit messages.
- If Git is handled manually by the user, simply report changed files and suggested commit scope.

---

## 9. Priority Rules

Prioritize:

```text
Color rough
→ prediction generation
→ candidate selection
→ hand mask
→ hand reference generation
→ save/export
```

Deprioritize:

```text
Search
3D / Blender
Auto body-part detection
Custom model training
Cloud features
Advanced asset management
```

unless explicitly requested.
