# State-machine contract

The workflow is linear unless a changed protected artifact invalidates downstream authorization.

```text
uninitialized
  → transcribing
  → awaiting_transcript_approval [STOP]
  → planning
  → awaiting_story_cut_approval [STOP, optional]
  → planning
  → previewing_current_clip
  → awaiting_current_preview_approval [STOP]
  → finalizing_current_clip
  → current_clip_complete [STOP]
  → previewing_current_clip (after explicit continuation)
  → all_clips_complete [STOP]
  → merge_approved (explicit request only)
  → complete
```

## Authorization scope

- Transcript approval authorizes planning from one exact transcript and project context.
- Story-cut approval authorizes one exact rough cut.
- Preview approval authorizes one exact preview plus one exact render recipe and editing-guide hash.
- Final completion authorizes no work on the next clip.
- Merge approval authorizes one merge of the recorded verified finals.

## Automatic invalidation

Refresh transcript review when source media, config, or discovered instruction content changes. Regenerate the current preview when the transcript, guide, preview, recipe, Remotion source, caption data, props, package lock, or assets change. Re-verify finals before merge if any final or verification file changes.

A filename is never authorization. Authorization is the recorded hash plus an approval receipt.
