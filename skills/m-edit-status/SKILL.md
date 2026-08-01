---
name: m-edit-status
description: Use when a user asks what a video-editing project completed, what is awaiting approval, whether protected files changed, why a gate is blocked, or how to resume.
license: MIT
compatibility: Requires read access to the project's `.m-edit` directory.
metadata:
  version: "1.0.0-rc.1"
---

# Report state without changing it

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


Run:

```bash
<suite-root>/bin/m-edit status --project "<video-folder>"
```

Report the current phase and clip, completed/pending clips, transcript and story-cut approvals, current preview version, recipe/code integrity, final verification, merge eligibility, warnings, and one exact next action. Do not create media or mutate state.
