---
name: m-edit-final
description: Use when the current clip's exact preview is explicitly approved and its individual high-quality final must be rendered and verified without creative drift.
license: MIT
compatibility: Requires Remotion and FFmpeg/FFprobe.
metadata:
  version: "1.0.0-rc.1"
---

# Render the approved final

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


Run:

```bash
<suite-root>/bin/m-edit guard --project "<video-folder>" --kind final --clip "<current-clip>"
<suite-root>/bin/m-edit recipe verify --project "<video-folder>" --recipe "<approved-recipe>"
```

Render from source masters and the hash-locked recipe, not from the compressed preview. The only intentional differences from preview are approved delivery settings such as resolution, codec, bitrate, CRF, and output path. Do not change timing, captions, composition, props, assets, crop, motion, or audio intent.

Verify all streams, full decode, dimensions, audio, contact sheet, duration parity, and visual fidelity against the approved preview:

```bash
<suite-root>/bin/m-edit verify \
  --input "<final>" \
  --output "<final-verification>" \
  --compare-preview "<approved-preview>" \
  --min-ssim "<configured-threshold>" \
  --contact-sheet "<final-contact-sheet>" \
  [--width N --height N --require-audio]
```

Inspect representative frames, write the final report, then record:

```bash
<suite-root>/bin/m-edit mark-final --project "<video-folder>" --clip "<current-clip>" --path "<final-relative-path>" --verification "<verification-relative-path>"
```

STOP. Do not edit the next clip or merge in the same turn.
