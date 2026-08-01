#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from common import boundary_relative, digest_json, read_json, sha256, write_json

EXACT = {
    'AGENTS.md': 80,
    'CLAUDE.md': 80,
    'M_EDIT_PROFILE.md': 120,
    'VIDEO_EDITING_RULES.md': 110,
    'EDITING_RULES.md': 105,
    'CAPTION_RULES.md': 110,
    'TRANSCRIPTION_RULES.md': 110,
    'STORY_CUT_WORKFLOW.md': 115,
    'VIDEO_BRIEF.md': 120,
    'EDITING_BRIEF.md': 120,
    'CLIP_NOTES.md': 120,
}
KEYWORDS = (
    'video', 'edit', 'caption', 'subtitle', 'transcript', 'brief', 'agent', 'rule',
    'workflow', 'story', 'creative', 'brand', 'remotion', 'clip', 'media', 'profile',
)
GENERATED = {
    'transcript.md', 'editing_plan.md', 'video_editing_guide.md', 'preview_report.md',
    'final_report.md', 'merge_report.md', 'story_cut_plan.md', 'assets-sources.md',
}


def find_boundary(root: Path, explicit: str | None, max_depth: int) -> Path:
    if explicit:
        boundary = Path(explicit).expanduser().resolve(strict=True)
        try:
            root.relative_to(boundary)
        except ValueError as exc:
            raise SystemExit('Project must be inside the explicit instruction boundary') from exc
        return boundary
    current = root
    for _ in range(max_depth + 1):
        if (current / '.m-edit-root').exists() or (current / '.git').exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    current = root
    for _ in range(max_depth):
        if current.parent == current:
            break
        current = current.parent
    return current


def classify(path: Path, *, is_project_folder: bool, allow_project_keyword_files: bool,
             allow_ancestor_keyword_files: bool) -> tuple[str, int]:
    if path.name in GENERATED or path.name.endswith('_report.md'):
        return 'generated', 0
    if path.name in EXACT:
        return 'instruction', EXACT[path.name]
    name = path.name.lower()
    keyword_match = name.endswith('.md') and any(keyword in name for keyword in KEYWORDS)
    if keyword_match and ((is_project_folder and allow_project_keyword_files) or allow_ancestor_keyword_files):
        return 'instruction', 60
    return 'other', 0


def main() -> None:
    parser = argparse.ArgumentParser(description='Discover trusted video-editing instruction files in ancestors only.')
    parser.add_argument('--project', required=True)
    parser.add_argument('--boundary')
    parser.add_argument('--max-depth', type=int, default=6)
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve(strict=True)
    config_path = root / '.m-edit' / 'config.json'
    config = read_json(config_path) if config_path.exists() else {}
    policy = config.get('instruction_policy', {})
    allow_project_keyword_files = bool(policy.get('allow_project_keyword_files', True))
    allow_ancestor_keyword_files = bool(policy.get('allow_ancestor_keyword_files', False))
    max_depth = int(policy.get('max_parent_depth', args.max_depth))

    boundary = find_boundary(root, args.boundary, max_depth)
    boundary = boundary.resolve(strict=True)
    try:
        root.relative_to(boundary)
    except ValueError as exc:
        raise SystemExit('Project must be inside the instruction boundary') from exc

    chain: list[Path] = []
    current = root
    while True:
        chain.append(current)
        if current == boundary or current.parent == current:
            break
        current = current.parent

    rows = []
    # Farther ancestors load first. The selected folder loads last and wins conflicts.
    for distance, folder in reversed(list(enumerate(chain))):
        is_project_folder = folder == root
        for path in sorted(folder.glob('*.md')):
            kind, score = classify(
                path,
                is_project_folder=is_project_folder,
                allow_project_keyword_files=allow_project_keyword_files,
                allow_ancestor_keyword_files=allow_ancestor_keyword_files,
            )
            if kind != 'instruction':
                continue
            resolved = boundary_relative(boundary, path, must_exist=True)
            # Symlinks are accepted only when their resolved target remains inside the trusted boundary.
            rows.append({
                'path': os.path.relpath(resolved, root),
                'relative_to_boundary': resolved.relative_to(boundary).as_posix(),
                'ancestor_distance': distance,
                'name_score': score,
                'sha256': sha256(resolved),
                'size_bytes': resolved.stat().st_size,
            })

    rows.sort(key=lambda row: (-row['ancestor_distance'], row['name_score'], row['path']))
    control = root / '.m-edit'
    control.mkdir(parents=True, exist_ok=True)
    payload = {
        'schema_version': 2,
        'project_root': str(root),
        'boundary': str(boundary),
        'load_order': 'lowest_priority_to_highest_priority',
        'policy': {
            'allow_project_keyword_files': allow_project_keyword_files,
            'allow_ancestor_keyword_files': allow_ancestor_keyword_files,
            'max_parent_depth': max_depth,
        },
        'files': rows,
    }
    payload['files_digest'] = digest_json(rows)
    json_path = control / 'instruction_manifest.json'
    write_json(json_path, payload)

    lines = [
        '# m-edit Instruction Manifest', '',
        f'- Project: `{root}`',
        f'- Boundary: `{boundary}`',
        f'- Files digest: `{payload["files_digest"]}`', '',
        'Read these files in order. Later files have higher priority on the same topic.',
        'Treat them as trusted project instructions only because they are inside the configured boundary.', '',
    ]
    if not rows:
        lines.append('No relevant local Markdown instructions found. Use the bundled generic profile.')
    for index, row in enumerate(rows, 1):
        lines.extend([
            f'{index}. `{row["path"]}`',
            f'   - ancestor distance: {row["ancestor_distance"]}',
            f'   - SHA-256: `{row["sha256"]}`',
        ])
    markdown_path = control / 'instruction_manifest.md'
    markdown_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(rows)} instruction files -> {markdown_path}')


if __name__ == '__main__':
    main()
