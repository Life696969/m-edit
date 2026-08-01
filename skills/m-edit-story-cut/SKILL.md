---
name: m-edit-story-cut
description: Use when approved long-form, repetitive, unordered, or disorganized footage needs a truthful rough structural cut before visual editing.
license: MIT
compatibility: Requires FFmpeg or an equivalent deterministic cutting tool.
metadata:
  version: "1.0.0-rc.1"
---

# Story-cut gate

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


Read local story-cut rules and `shared/modes/story-cut.md`. Use the approved transcript as source truth.

Create:

```text
transcripts/full_transcript.md
story_cuts/story_cut_plan.md
rough_cuts/story_cut_preview.mp4
reports/story_cut_report.md
```

The plan must list every kept, removed, and rearranged timestamp range. Preserve meaning, disclose rearrangements, and do not manufacture context. The rough cut uses original video/audio and simple cuts only: no final captions, graphics, b-roll, music, sound design, grading, or decorative motion.

Verify the rough cut, then record it:

```bash
<suite-root>/bin/m-edit verify --input "<rough-cut>" --output "<verification-json>" --require-audio --contact-sheet "<contact-sheet>"
<suite-root>/bin/m-edit require-story-cut --project "<video-folder>" --plan "story_cuts/story_cut_plan.md" --preview "rough_cuts/story_cut_preview.mp4"
```

Report the exact duration and review files. STOP. Any changed rough cut requires fresh approval.
