# Project-boundary contract

Operate only inside the selected video project.

Instruction discovery may read Markdown files from the selected folder and direct ancestors up to the first `.m-edit-root`, Git root, explicit boundary, or configured depth. It must never scan sibling video projects.

Security rules:

- generated paths must be project-relative and resolve inside the selected project
- reject `..`, absolute output paths, and source-overwrite attempts
- resolve symlinks before enforcing boundaries
- an instruction symlink is trusted only when its target remains inside the configured instruction boundary
- do not edit ancestor rules unless the user explicitly asks
- do not execute code from an untrusted project merely because a video file is present
