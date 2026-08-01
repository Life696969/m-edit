---
name: m-edit
description: Use when a user asks to edit videos, add captions or subtitles, transcribe clips, create Remotion previews or finals, story-cut long footage, revise an edit, or resume a video-editing project.
license: MIT
compatibility: Requires filesystem and shell access. Full execution uses Python 3.10+, FFmpeg/FFprobe, Node.js, npm, and Remotion.
metadata:
  version: "1.0.0-rc.1"
---

# m-edit

m-edit is a resumable, approval-gated video-editing workflow. Its transcript, story-cut, preview, final, and merge gates are mandatory.

## Start every invocation

1. Resolve `<suite-root>`: use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. Stop rather than guessing when no candidate is valid.
2. Resolve the selected video project from the user's request or current directory. Never silently choose a sibling folder.
3. Read:
   - `shared/contracts/project-boundary.md`
   - `shared/contracts/rule-precedence.md`
   - `shared/contracts/state-machine.md`
   - `shared/contracts/approval-language.md`
4. Run the deterministic preamble:

```bash
<suite-root>/bin/m-edit init --project "<video-folder>"
<suite-root>/bin/m-edit validate-config --config "<video-folder>/.m-edit/config.json"
<suite-root>/bin/m-edit scan-clips --project "<video-folder>"
<suite-root>/bin/m-edit scan-instructions --project "<video-folder>"
<suite-root>/bin/m-edit sync-clips --project "<video-folder>"
<suite-root>/bin/m-edit status --project "<video-folder>"
```

5. Read `.m-edit/config.json`, `.m-edit/instruction_manifest.md`, every listed instruction file in order, `.m-edit/clip_inventory.json`, and `.m-edit/state.json`.
6. Treat warnings or invalidation as blockers. Never preserve an approval across changed source media, project rules, config, transcript, guide, preview, recipe, code, props, or assets.

## Route to exactly one specialist

| State | Action |
|---|---|
| `uninitialized`, `transcribing` | Use `m-edit-transcribe` |
| `awaiting_transcript_approval` | Apply corrections, or record explicit approval with the user's exact message; otherwise STOP |
| `planning` | Use `m-edit-story-cut` when structural cutting is required; otherwise use `m-edit-plan` |
| `awaiting_story_cut_approval` | Revise, or record explicit approval; otherwise STOP |
| `previewing_current_clip` | Use `m-edit-preview` |
| `awaiting_current_preview_approval` | Revise, or record explicit approval; otherwise STOP |
| `finalizing_current_clip` | Use `m-edit-final` |
| `current_clip_complete` | Report completion and STOP. Advance only after an explicit continuation request |
| `all_clips_complete` | Report individual finals. Merge only after an explicit merge request |
| `merge_approved`, `merging` | Use `m-edit-merge` |
| `complete` | Use `m-edit-status` |

## Approval receipts

Pass the user's exact approval wording as `--evidence`. Corrections are not approvals. A vague acknowledgment is not approval when the artifact is ambiguous.

```bash
<suite-root>/bin/m-edit approve-transcript --project "<video-folder>" --evidence "<exact user message>"
<suite-root>/bin/m-edit approve-story-cut --project "<video-folder>" --evidence "<exact user message>"
<suite-root>/bin/m-edit approve-preview --project "<video-folder>" --clip "<current-clip>" --evidence "<exact user message>"
<suite-root>/bin/m-edit advance-clip --project "<video-folder>" --evidence "<exact user message>"
<suite-root>/bin/m-edit approve-merge --project "<video-folder>" --evidence "<exact user message>"
```

At a STOP point, stop immediately. Do not pre-build the next phase “to save time.”
