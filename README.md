# m-edit

A generic, open-source Agent Skill suite for editing videos with Remotion.

m-edit turns a folder of source media into a resumable, approval-gated workflow:

```text
Discover trusted project rules and source clips
→ transcribe every clip
→ human transcript approval
→ optional story-cut approval
→ creative and Remotion plan
→ one clip preview + hash-locked render recipe
→ human preview approval
→ verified final matching the preview
→ explicit continuation to the next clip
→ optional explicit merge
```

It supports talking-head videos, tutorials, screen recordings, podcasts, interviews, product demos, slideshows, montages, cinematic edits, long story cuts, and mixed formats. It does not assume a creator, language, font, color, caption position, platform, or recurring effect.

## Why m-edit is different

- **Approvals are artifact-bound.** A filename is not approval; hashes and receipts are recorded.
- **Preview approval locks the implementation.** Remotion code, caption data, props, assets, source clip, and package lock are captured in a render recipe.
- **Source and rule changes invalidate downstream work.** Files are checked directly, not only through a cached manifest.
- **Finals are compared with approved previews.** Duration and SSIM checks detect creative drift.
- **One current clip at a time.** Completing a clip does not silently authorize the next one.
- **Network access is off by default.** Models, packages, fonts, and assets are never downloaded without authorization.
- **State survives sessions.** `.m-edit/state.json` makes the workflow inspectable and resumable.
- **A neutral Remotion starter is bundled.** It provides media fitting and data-driven captions without imposing a creator style.
- **Caption data is portable.** SRT, VTT, and common JSON can be normalized, validated, chunked, and exported.

## Requirements

Core workflow:

- Python 3.10+
- FFmpeg and FFprobe
- filesystem and shell access

Rendering:

- Node.js and npm
- an existing Remotion project, or user authorization to create one

Transcription:

- adjacent `.srt`, `.vtt`, or compatible JSON; or
- a local OpenAI Whisper, faster-whisper, or whisper.cpp provider; or
- a host agent that can genuinely inspect audio

m-edit does not send media to a remote service by default.

## Install

### Claude Code plugin

From a local checkout during development:

```bash
claude --plugin-dir .
```

After publishing the repository as a Claude marketplace:

```text
/plugin marketplace add OWNER/REPOSITORY
/plugin install m-edit@m-edit
/reload-plugins
```

Claude plugin skills are namespaced, for example `/m-edit:m-edit`.

### Manual install: Claude, Codex, or Agent Skills

```bash
./install.sh --host claude
./install.sh --host codex
./install.sh --host agents
./install.sh --host all
```

Windows PowerShell:

```powershell
.\install.ps1 -HostName claude
.\install.ps1 -HostName codex
.\install.ps1 -HostName all
```

Project-local installation is supported:

```bash
./install.sh --host codex --scope project --project-dir /path/to/project
```

Uninstall without deleting project state:

```bash
./uninstall.sh --host all
```

## First run

Open the coding agent in a trusted folder containing source videos and invoke m-edit:

```text
Edit these videos and add captions using m-edit.
```

Or invoke the installed skill directly, such as `$m-edit` in Codex. The first phase creates only:

```text
.m-edit/
transcript.md
editing_plan.md
```

It then stops for transcript review.

## Project outputs

Default layout:

```text
m-edit-output/<project-slug>/
  previews/
  finals/
  reports/
  screenshots/
  recipes/
  assets/
    external/
    generated/
    sources.md
```

Raw source files are never intentional output targets.

## Local customization

Place project rules in the selected folder or trusted ancestors:

- `M_EDIT_PROFILE.md`
- `VIDEO_EDITING_RULES.md`
- `CAPTION_RULES.md`
- `TRANSCRIPTION_RULES.md`
- `STORY_CUT_WORKFLOW.md`
- `VIDEO_BRIEF.md`
- `CLIP_NOTES.md`
- `AGENTS.md` or `CLAUDE.md`

Later/nearer rules have higher priority, but they cannot disable the fixed approval and source-preservation invariants. See [Customization](docs/CUSTOMIZATION.md).

## Command line

The bundled CLI is used by the skills and is also useful for diagnostics:

```bash
bin/m-edit doctor --project .
bin/m-edit status --project .
bin/m-edit transcribe detect
bin/m-edit captions validate --input captions.json
bin/m-edit captions chunk --input captions.json --output caption-chunks.json --max-words 4
bin/m-edit scaffold-remotion --project .
bin/m-edit recipe verify --project . --recipe path/to/recipe.json
```

## Safety

Only run m-edit in trusted workspaces. Remotion projects execute Node.js code, and a Markdown skill cannot sandbox an agent. Review commands and third-party dependencies before authorizing them. See [Threat model](docs/THREAT_MODEL.md) and [Security policy](SECURITY.md).

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 shared/scripts/release_audit.py --root .
python3 scripts/validate_skills.py
```

The repository includes deterministic state/security tests, trigger-description tests, installer tests, generated-media integration tests, and a model-evaluation harness. See [Evaluation](docs/EVALUATION.md).

## Status

`1.0.0-rc.1` is a release candidate. The deterministic workflow and integrity layer are tested; creative output quality still depends on source material, the coding agent, transcription quality, Remotion implementation, and human review.

## License

MIT. External assets and user media retain their own licenses.
