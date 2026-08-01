# Validation status

Version: `1.0.0-rc.1`

Validated locally on August 1, 2026 in a Linux environment with Python 3.13, Node.js 22, npm 10, and FFmpeg 7.

## Passed locally

- 46 deterministic unit and integration tests across workflow, captions, transcription, instruction discovery, installers, recipes, media verification, scaffold generation, trigger descriptions, sanitization, and packaging
- complete generated-video workflow from initialization through transcript approval, guide recording, preview recipe, preview approval, final-to-preview comparison, and `all_clips_complete`
- full source-content hashing and direct instruction-file hashing
- source-content mutation blocking without false invalidation from timestamp-only changes under full hashing
- atomic state writes and project lock behavior
- exact approval receipts for transcript, story cut, preview, continuation, and merge
- wrong-clip, path-traversal, sibling-folder, and symlink-boundary rejection
- preview, guide, caption/code/asset recipe, and final drift blocking
- all-stream FFmpeg decode, dimension/audio checks, contact sheets, duration parity, and SSIM comparison
- SRT, standard WebVTT, common JSON, word-timestamp chunking, validation, and SRT export
- offline-first transcription behavior; no implicit model download
- neutral Remotion scaffold creation without package installation
- global and project-local shell installation, same-version protection, force backup, dry run, and uninstall preservation
- Agent Skills metadata, trigger descriptions, independent suite-root bootstrap, and explicit STOP markers
- deterministic ZIP creation and checksum generation
- generic secret/path/binary audit plus an optional external private denylist
- a private release audit using an uncommitted denylist for creator-specific material; no matches remained

## Prepared for CI, not executed in this environment

- Python 3.10 and 3.13 matrix on Linux, macOS, and Windows
- PowerShell installer and uninstaller smoke test on Windows
- deterministic release packaging after all platform tests
- tagged GitHub release workflow

## Evidence still required before calling stable behavior “10/10”

- black-box pressure evaluations on real Claude Code and Codex installations
- successful edits of representative talking-head, tutorial, podcast/interview, product-demo, montage, slideshow, story-cut, and mixed-format projects
- actual `npm install`, TypeScript compile, Remotion Studio, preview render, and final render of the bundled starter on supported platforms
- Claude plugin validation and marketplace install/update test
- official Agent Skills validator run when available in the release environment
- Windows PowerShell execution, which could not be run in this Linux environment

The repository is release-engineered as a strong public release candidate. Stable `1.0.0` should be cut only after the empirical items above pass and their reports are attached.
