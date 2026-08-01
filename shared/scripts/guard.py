#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, sha256
from recipe import verify as verify_recipe
from state import guard_context, guard_guide, guard_transcript, safe_output, validate_verification


def main() -> None:
    parser = argparse.ArgumentParser(description='Block unsafe m-edit transitions before work starts.')
    parser.add_argument('--project', required=True)
    parser.add_argument('--kind', choices=['preview', 'final', 'merge'], required=True)
    parser.add_argument('--clip')
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    state = read_json(root / '.m-edit' / 'state.json')

    guard_context(root, state)
    guard_transcript(root, state)

    if args.kind in {'preview', 'final'}:
        guard_guide(root, state)

    if args.kind == 'preview':
        if state['phase'] != 'previewing_current_clip':
            raise SystemExit(f'BLOCKED: preview is not allowed from {state["phase"]}')
        if args.clip and args.clip != state.get('current_clip'):
            raise SystemExit('BLOCKED: target is not the current clip')

    elif args.kind == 'final':
        if state['phase'] != 'finalizing_current_clip':
            raise SystemExit(f'BLOCKED: final is not allowed from {state["phase"]}')
        clip = args.clip or state.get('current_clip')
        if clip != state.get('current_clip'):
            raise SystemExit('BLOCKED: target is not the current clip')
        record = state['clips'][clip]
        preview, _ = safe_output(root, state, record['preview_path'])
        if sha256(preview) != record.get('approved_preview_hash'):
            raise SystemExit('BLOCKED: approved preview changed')
        recipe_path, _ = safe_output(root, state, record['recipe_path'])
        payload = verify_recipe(root, recipe_path)
        if sha256(recipe_path) != record.get('approved_recipe_hash'):
            raise SystemExit('BLOCKED: approved render recipe changed')
        if payload.get('bundle_digest') != record.get('approved_recipe_bundle_digest'):
            raise SystemExit('BLOCKED: Remotion code, caption data, props, or assets changed after preview approval')
        if record.get('approved_guide_hash') != state['guide']['hash']:
            raise SystemExit('BLOCKED: editing guide changed after preview approval')

    else:
        if state['phase'] != 'merge_approved' or not state['merge'].get('approved'):
            raise SystemExit('BLOCKED: merge was not explicitly approved')
        for clip in state['clip_order']:
            record = state['clips'][clip]
            if record.get('status') != 'complete':
                raise SystemExit(f'BLOCKED: incomplete final for {clip}')
            final, _ = safe_output(root, state, record['final_path'])
            if sha256(final) != record.get('final_hash'):
                raise SystemExit(f'BLOCKED: final changed for {clip}')
            verification, _ = safe_output(root, state, record['verification_path'])
            validate_verification(final, verification)

    print(f'ALLOWED: {args.kind}')


if __name__ == '__main__':
    main()
