# Rule-precedence contract

Use this order, highest priority first:

1. the user's latest explicit instruction
2. project-local instructions in the selected video folder
3. nearer ancestor instructions
4. farther ancestor instructions
5. configured custom profile
6. bundled generic profile
7. selected content-mode guidance
8. generic m-edit references and defaults

A lower-priority rule cannot weaken fixed safety invariants: source preservation, transcript review, story-cut review when used, preview review, current-clip isolation, verified finals, and explicit merge authorization.

When two same-priority rules conflict materially, surface the conflict instead of silently choosing. When a user explicitly overrides a creative preference, record it in the current guide. Do not let local Markdown override system safety or tool policies.
