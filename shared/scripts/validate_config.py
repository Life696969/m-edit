#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import read_json

REQUIRED_TRUE = (
    'one_clip_at_a_time',
    'transcript_approval_required',
    'story_cut_approval_required',
    'preview_approval_required',
    'merge_requires_explicit_request',
)


def validate(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get('schema_version') != 2:
        errors.append('schema_version must be 2')
    if config.get('source_hash_mode') not in {'full', 'stat'}:
        errors.append('source_hash_mode must be full or stat')
    output_root = config.get('output_root')
    if not isinstance(output_root, str) or not output_root or Path(output_root).is_absolute() or '..' in Path(output_root).parts:
        errors.append('output_root must be a non-empty project-relative path without ..')
    workflow = config.get('workflow')
    if not isinstance(workflow, dict):
        errors.append('workflow must be an object')
    else:
        for field in REQUIRED_TRUE:
            if workflow.get(field) is not True:
                errors.append(f'workflow.{field} is a fixed safety invariant and must be true')
    instruction = config.get('instruction_policy')
    if not isinstance(instruction, dict):
        errors.append('instruction_policy must be an object')
    else:
        depth = instruction.get('max_parent_depth')
        if not isinstance(depth, int) or not 0 <= depth <= 20:
            errors.append('instruction_policy.max_parent_depth must be an integer from 0 to 20')
    render = config.get('render')
    if not isinstance(render, dict):
        errors.append('render must be an object')
    else:
        ssim = render.get('fidelity_min_ssim')
        if not isinstance(ssim, (int, float)) or not 0 <= ssim <= 1:
            errors.append('render.fidelity_min_ssim must be between 0 and 1')
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate m-edit config and fixed workflow invariants.')
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    path = Path(args.config).expanduser().resolve(strict=True)
    errors = validate(read_json(path))
    if errors:
        raise SystemExit('\n'.join(f'- {error}' for error in errors))
    print(f'valid: {path}')


if __name__ == '__main__':
    main()
