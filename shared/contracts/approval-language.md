# Approval-language contract

Approval must clearly refer to the artifact currently awaiting review. Store the user's exact wording in `.m-edit/approvals.jsonl`.

Examples:

- transcript: `transcript approved`, `the transcript is correct`, `continue with this transcript`
- story cut: `story cut approved`, `use this rough cut`
- preview: `preview approved`, `render this clip's final`
- continuation: `continue to the next clip`, `edit clip 2 now`
- merge: `merge the verified final clips`, `combine all finals`

Do not treat these as approval when the target is ambiguous:

- `okay`, `nice`, `looks better`, or an emoji
- a correction or change request
- approval of a different artifact
- a request to discuss something else
- silence or elapsed time

After any correction, the changed artifact requires review again. Approval in one language is valid; exact English keywords are not required. The agent must understand that the user intentionally accepted the current artifact.
