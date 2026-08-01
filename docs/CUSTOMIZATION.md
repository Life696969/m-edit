# Customization

m-edit is intentionally generic. Project-specific preferences belong in local Markdown files rather than the public skill.

## Recommended profile

Create `M_EDIT_PROFILE.md` in the project or a trusted parent:

```markdown
# Video profile

## Audience and platform
- Target viewer:
- Platform:
- Default aspect ratio:

## Captions
- Language/script:
- Typeface or fallback:
- Base placement:
- Emphasis:

## Visual system
- Colors:
- Motion style:
- Framing rules:
- Recurring motifs:

## Audio and assets
- Music policy:
- Sound effects:
- External asset policy:
```

## Precedence

Selected-folder rules beat ancestor rules. Nearer ancestors beat farther ancestors. Custom rules cannot disable fixed transcript, preview, source-preservation, verification, or explicit-merge gates.

## Instruction trust

By default, keyword-matched Markdown is discovered only in the selected folder. Ancestors require recognized filenames. Set `instruction_policy.allow_ancestor_keyword_files` only when the ancestor tree is trusted and deliberately organized for m-edit.
