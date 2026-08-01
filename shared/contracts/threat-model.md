# Threat model

m-edit operates on local media and code, both of which may be untrusted.

## Main risks

- path traversal or symlink escape
- source overwrite
- prompt injection in ancestor Markdown
- malicious or resource-exhausting media
- network access from FFmpeg, Remotion, packages, models, or assets
- arbitrary Node execution in an untrusted Remotion project
- approval spoofing or stale approval reuse
- code/asset drift between preview and final
- unlicensed external media

## Mitigations

- project-relative output enforcement and resolved-path checks
- trusted ancestor boundary and conservative instruction discovery
- full SHA-256 source hashes by default
- FFmpeg protocol restrictions and timeouts
- no dependency/model/asset downloads by default
- approval receipts plus artifact hashes
- render-recipe hash lock
- full media decode and preview/final comparison
- source ledger and explicit license basis

## Residual risk

A Markdown skill cannot sandbox a coding agent or make an untrusted Node project safe. Run m-edit only in trusted workspaces with narrow filesystem permissions. Review shell commands and third-party dependencies before authorizing them.
