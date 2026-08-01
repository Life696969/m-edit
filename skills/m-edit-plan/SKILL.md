---
name: m-edit-plan
description: Use when a video's transcript is approved and the project needs a complete creative, caption, asset, accessibility, and Remotion execution guide before preview rendering.
license: MIT
compatibility: Requires source-media and project-file access.
metadata:
  version: "1.0.0-rc.1"
---

# Plan the approved edit

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


## Preconditions

Confirm state is `planning`. Run status and stop on any integrity warning. Read all project instructions, approved transcript, provisional plan, source clips, selected profile and mode, and these references:

- `shared/references/captions.md`
- `shared/references/creative-direction.md`
- `shared/references/remotion-project.md`
- `shared/contracts/external-assets.md`
- `shared/contracts/remotion-execution.md`
- `shared/contracts/verification.md`

If the footage needs truthful structural cutting before visual treatment, use `m-edit-story-cut` instead of creating the guide.

## Produce `video_editing_guide.md`

The guide must specify:

1. viewer, platform, purpose, opening, payoff, proof, ending, and likely drop-off points
2. role and exact source range for every clip
3. output dimensions, FPS, safe zones, crop behavior, and accessibility constraints
4. caption source, chunking, placement logic, emphasis, collision behavior, and timing data path
5. coherent typography, motion, framing, transition, asset, and audio systems
6. purposeful visual variation without forcing effects
7. Remotion project findings, compositions, entry point, reusable components, caption data, props, asset paths, and commands
8. versioned preview/final filenames and verification criteria
9. external-asset source ledger requirements
10. the one-clip-at-a-time approval sequence

Do not assume vertical video, a particular language, font, color, caption position, or editing style.

If no Remotion project exists, scaffold the bundled neutral project without network access:

```bash
<suite-root>/bin/m-edit scaffold-remotion --project "<video-folder>" --target "m-edit-remotion"
```

Explain the dependencies before running `npm install`. User authorization is required for dependency installation or any network access. The starter is a foundation, not a mandatory visual style.

Record the guide:

```bash
<suite-root>/bin/m-edit record-guide --project "<video-folder>"
```

Continue only to `m-edit-preview` for the current clip.
