---
name: m-edit-preview
description: Use when an approved editing guide exists and exactly one current clip needs a Remotion preview, layout check, caption pass, or revision.
license: MIT
compatibility: Requires an existing or explicitly approved-to-create Remotion project.
metadata:
  version: "1.0.0-rc.1"
---

# Build one preview

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


## Iron rule

Edit only `.m-edit/state.json.current_clip`. Do not implement or render another clip. Do not merge.

Run the guard:

```bash
<suite-root>/bin/m-edit guard --project "<video-folder>" --kind preview --clip "<current-clip>"
```

Read the current clip's guide section, re-inspect the source, and load current official Remotion best practices when available.

## Implement

1. Preserve source media.
2. Keep approved transcript/caption timing in canonical JSON separate from visual components. Use `m-edit captions chunk` only when chunking is specified in the guide; preserve exact words and prefer word timestamps when available.
3. Implement only the approved current-clip treatment.
4. Use deterministic frame-based Remotion animation.
5. Keep external assets inside the output asset folder and update the source ledger.
6. Render representative stills before the full preview when layout, crop, or collision risk is high.
7. Create a versioned preview matching final timing and layout intent.
8. Create a render recipe that hashes the source clip, Remotion entry point and relevant source tree, caption data, input props, assets, and package lock:

```bash
<suite-root>/bin/m-edit recipe create \
  --project "<video-folder>" \
  --clip "<current-clip>" \
  --composition-id "<composition-id>" \
  --entry-point "<entry-file>" \
  --package-lock "<package-lock>" \
  --render-command "<deterministic command/template>" \
  --include "<Remotion source directory>" \
  --include "<caption-data>" \
  --include "<asset directory>" \
  --output "<recipe-json>"
```

9. Verify the preview and create a contact sheet:

```bash
<suite-root>/bin/m-edit verify --input "<preview>" --output "<preview-verification>" --contact-sheet "<contact-sheet>" [--require-audio]
```

10. Write the preview report and record all three artifacts:

```bash
<suite-root>/bin/m-edit await-preview \
  --project "<video-folder>" \
  --clip "<current-clip>" \
  --path "<preview-relative-path>" \
  --recipe "<recipe-relative-path>" \
  --verification "<preview-verification-relative-path>"
```

STOP. A revision creates a new preview, verification, recipe, and approval.
