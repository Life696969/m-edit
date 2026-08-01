# Architecture

## Design principles

1. **Human approval at irreversible interpretation points.** Transcript, story cut, preview, and merge are separate gates.
2. **File-based state.** The project remains understandable and resumable without a server.
3. **Progressive disclosure.** A thin router loads only the specialist skill, mode, contracts, and references required for the current phase.
4. **Mechanical rules become code.** Path, hash, source, state, recipe, verification, and merge constraints are scripts rather than prose promises.
5. **Judgment remains explicit.** Creative direction and caption quality stay human-reviewable artifacts.
6. **No hidden network dependency.** Local assets and providers are preferred; downloads require authorization.

## Layers

```text
User request / direct skill invocation
  ↓
m-edit router
  ↓
Phase specialist
  ↓
Local project instructions + generic profile + content mode
  ↓
Human-readable artifacts
  ↓
State, guard, recipe, inventory, transcription, and verification tools
  ↓
Remotion implementation and media outputs
```

## Protected context

Transcript approval binds:

- source clip inventory and direct source hashes
- config
- instruction manifest and direct instruction-file hashes
- transcript

Preview approval additionally binds:

- editing guide
- preview
- render recipe file
- render recipe bundle digest covering code, captions, props, assets, source clip, and package lock

Final verification binds:

- final media hash
- all-stream decode
- expected delivery properties
- duration parity and SSIM against approved preview

## State

`.m-edit/state.json` stores phase, clip order, current clip, artifact paths, hashes, recipe digests, approvals, finals, and history. `.m-edit/approvals.jsonl` stores exact user approval evidence.

Writes are atomic and state transitions use a project lock. Status is read-only.

## Trust boundaries

- output must remain inside the selected project
- instruction files must remain inside the configured ancestor boundary
- symlinks are resolved before boundary checks
- sibling projects are never scanned
- project Node code remains outside m-edit's sandbox and must be trusted

## Distribution

The repository is simultaneously:

- a Claude Code plugin/marketplace
- a manually installable Claude skill suite
- a Codex skill suite
- a generic Agent Skills installation

Claude plugin installation uses the plugin root. Manual installation uses versioned releases under `~/.m-edit/` or a project-local `.m-edit-suite/`.
