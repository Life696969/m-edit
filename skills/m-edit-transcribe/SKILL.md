---
name: m-edit-transcribe
description: Use when a video project has no approved transcript, spoken media needs timestamped transcription, or source clips, config, or editing rules changed after transcript approval.
license: MIT
compatibility: Requires media inspection capability or an existing/local transcription provider.
metadata:
  version: "1.0.0-rc.1"
---

# Transcribe before editing

**Resolve `<suite-root>` first:** use `${CLAUDE_PLUGIN_ROOT}` when it contains `shared/`; otherwise `${M_EDIT_HOME}/current`; otherwise the nearest `.m-edit-suite/current` above the video project; otherwise `~/.m-edit/current`. Confirm `VERSION`, `bin/m-edit`, and `shared/scripts/state.py` exist. If none is valid, stop with installation guidance.


## Iron gate

This phase may inspect and document media. It may not create target Remotion compositions, cuts, downloaded assets, previews, or finals.

## Load context

Resolve `<suite-root>`, then read:

- all files in `.m-edit/instruction_manifest.md`
- `shared/profiles/generic/profile.md`
- the configured custom profile, if any
- `shared/references/transcription.md`
- `shared/references/captions.md`
- `shared/references/content-mode-routing.md`
- the selected mode reference
- `shared/contracts/artifact-contract.md`

Run:

```bash
<suite-root>/bin/m-edit begin-transcription --project "<video-folder>" --reason "transcription started or context refreshed"
<suite-root>/bin/m-edit transcribe detect
```

## Transcription sources

Use the best available source in this order:

1. user-provided or adjacent `.srt`, `.vtt`, or compatible JSON
2. a configured local Whisper provider through `m-edit transcribe run`
3. the host agent's genuine audio-inspection capability

Never claim to have heard audio that the host cannot inspect. Never invent words. Mark uncertainty as `[unclear]`.

When the CLI can transcribe, store canonical per-clip data under `.m-edit/transcripts/`:

```bash
<suite-root>/bin/m-edit transcribe run --project "<video-folder>" --clip "<clip>" --output ".m-edit/transcripts/<clip-stem>.json"
<suite-root>/bin/m-edit captions validate --input "<video-folder>/.m-edit/transcripts/<clip-stem>.json"
```

## Required outputs

Create `transcript.md` and `editing_plan.md` from the templates. For every clip include exact filename, metadata, visual notes, phrase timestamps, exact spoken wording, uncertainties, and content-order reasoning. The provisional plan may identify roles and opportunities but does not authorize editing.

Record the gate:

```bash
<suite-root>/bin/m-edit await-transcript --project "<video-folder>"
```

Report clip count, created files, uncertain words, and facts needing review. STOP.
