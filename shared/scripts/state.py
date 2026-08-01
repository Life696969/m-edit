#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from common import (
    append_jsonl,
    digest_json,
    now,
    project_lock,
    project_relative,
    read_json,
    sha256,
    write_json,
)
from recipe import verify as verify_recipe

PHASES = {
    'uninitialized', 'transcribing', 'awaiting_transcript_approval', 'planning',
    'awaiting_story_cut_approval', 'previewing_current_clip',
    'awaiting_current_preview_approval', 'finalizing_current_clip',
    'current_clip_complete', 'all_clips_complete', 'merge_approved', 'merging', 'complete',
}


def suite_root() -> Path:
    return Path(__file__).resolve().parents[1]


def paths(project: str) -> tuple[Path, Path, Path]:
    root = Path(project).expanduser().resolve()
    control = root / '.m-edit'
    return root, control, control / 'state.json'


def load(project: str) -> tuple[Path, Path, Path, dict[str, Any]]:
    root, control, state_path = paths(project)
    if not state_path.exists():
        raise SystemExit(f'Missing {state_path}; run init')
    data = read_json(state_path)
    if data.get('schema_version') != 2:
        raise SystemExit('Unsupported state schema; run the migration or start a new .m-edit state directory')
    if data.get('phase') not in PHASES:
        raise SystemExit(f'Invalid phase: {data.get("phase")}')
    return root, control, state_path, data


def save(path: Path, data: dict[str, Any], event: str) -> None:
    data['updated_at'] = now()
    history = data.setdefault('history', [])
    history.append({'at': data['updated_at'], 'phase': data['phase'], 'event': event})
    if len(history) > 2000:
        del history[:-2000]
    write_json(path, data)


def source_paths(data: dict[str, Any]) -> set[str]:
    return set(data.get('clip_order', []))


def safe_output(root: Path, data: dict[str, Any], value: str, *, must_exist: bool = True) -> tuple[Path, str]:
    path, relative = project_relative(root, value, must_exist=must_exist)
    if relative in source_paths(data):
        raise SystemExit('Generated output may not overwrite a source clip')
    return path, relative


def fresh_clip_record(fingerprint: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        'status': 'pending',
        'source_fingerprint': fingerprint,
        'preview_version': 0,
        'preview_path': None,
        'preview_hash': None,
        'preview_verification_path': None,
        'recipe_path': None,
        'recipe_hash': None,
        'recipe_bundle_digest': None,
        'approved_preview_hash': None,
        'approved_recipe_hash': None,
        'approved_recipe_bundle_digest': None,
        'approved_guide_hash': None,
        'preview_approval_receipt_id': None,
        'final_path': None,
        'final_hash': None,
        'verification_path': None,
    }


def invalidate_downstream(data: dict[str, Any]) -> None:
    data['guide']['hash'] = None
    data['story_cut'] = {
        'required': False,
        'plan_path': None,
        'preview_path': None,
        'preview_hash': None,
        'approved_hash': None,
        'approval_receipt_id': None,
    }
    data['merge'] = {
        'approved': False,
        'approval_receipt_id': None,
        'path': None,
        'hash': None,
        'verification_path': None,
    }
    for name, clip in data.get('clips', {}).items():
        fingerprint = clip.get('source_fingerprint')
        data['clips'][name] = fresh_clip_record(fingerprint)


def context_paths(root: Path, data: dict[str, Any]) -> dict[str, Path]:
    context = data['context']
    return {
        'instruction_manifest_hash': root / context['instruction_manifest_path'],
        'config_hash': root / context['config_path'],
        'clip_inventory_hash': root / context['clip_inventory_path'],
    }


def verify_instruction_sources(root: Path, manifest: dict[str, Any]) -> None:
    boundary = Path(str(manifest.get('boundary', root))).expanduser().resolve(strict=True)
    try:
        root.resolve().relative_to(boundary)
    except ValueError as exc:
        raise SystemExit('Instruction boundary no longer contains the selected project') from exc
    for record in manifest.get('files', []):
        candidate = (root / str(record.get('path'))).resolve(strict=True)
        try:
            candidate.relative_to(boundary)
        except ValueError as exc:
            raise SystemExit(f'Instruction path escaped the trusted boundary: {record.get("path")}') from exc
        if sha256(candidate) != record.get('sha256'):
            raise SystemExit(f'Instruction file changed: {record.get("path")}')


def verify_source_inventory(root: Path, inventory: dict[str, Any]) -> None:
    clips = inventory.get('clips')
    if not isinstance(clips, list) or not clips:
        raise SystemExit('No source clips are recorded in the inventory')
    for record in clips:
        path, relative = project_relative(root, str(record.get('path')), must_exist=True)
        fingerprint = record.get('fingerprint') or {}
        stat = path.stat()
        if stat.st_size != fingerprint.get('size_bytes'):
            raise SystemExit(f'Source clip size changed: {relative}')
        if fingerprint.get('hash_mode') == 'full':
            expected = fingerprint.get('sha256')
            if not expected or sha256(path) != expected:
                raise SystemExit(f'Source clip content changed: {relative}')
        elif stat.st_mtime_ns != fingerprint.get('mtime_ns'):
            raise SystemExit(f'Source clip timestamp changed under stat-only hashing: {relative}')


def current_context_digest(root: Path, data: dict[str, Any], *, verify_sources: bool = True) -> str:
    values: dict[str, str] = {}
    for field, path in context_paths(root, data).items():
        if not path.exists():
            raise SystemExit(f'Missing context artifact: {path}')
        values[field] = sha256(path)
    manifest = read_json(context_paths(root, data)['instruction_manifest_hash'])
    inventory = read_json(context_paths(root, data)['clip_inventory_hash'])
    verify_instruction_sources(root, manifest)
    if verify_sources:
        verify_source_inventory(root, inventory)
    values['instruction_files_digest'] = str(manifest.get('files_digest') or digest_json(manifest.get('files', [])))
    values['source_records_digest'] = digest_json(inventory.get('clips', []))
    return digest_json(values)


def record_context(root: Path, data: dict[str, Any]) -> None:
    values = context_paths(root, data)
    for field, path in values.items():
        if not path.exists():
            raise SystemExit(f'Missing context artifact: {path}')
        data['context'][field] = sha256(path)
    data['context']['context_digest'] = current_context_digest(root, data)


def guard_context(root: Path, data: dict[str, Any]) -> None:
    for field, path in context_paths(root, data).items():
        expected = data['context'].get(field)
        if not expected or not path.exists() or sha256(path) != expected:
            raise SystemExit(f'Approved project context changed: {field}')
    actual_digest = current_context_digest(root, data)
    if not data['context'].get('context_digest') or actual_digest != data['context']['context_digest']:
        raise SystemExit('Approved project context changed: source or instruction content mismatch')


def guard_transcript(root: Path, data: dict[str, Any]) -> None:
    transcript, _ = project_relative(root, data['transcript']['path'], must_exist=True)
    approved = data['transcript'].get('approved_hash')
    if not approved or sha256(transcript) != approved:
        raise SystemExit('Approved transcript hash mismatch')


def guard_guide(root: Path, data: dict[str, Any]) -> None:
    guide, _ = project_relative(root, data['guide']['path'], must_exist=True)
    expected = data['guide'].get('hash')
    if not expected or sha256(guide) != expected:
        raise SystemExit('Editing guide hash mismatch')


def record_approval(control: Path, kind: str, artifact_hash: str, evidence: str) -> str:
    evidence = (evidence or '').strip()
    if len(evidence) < 2:
        raise SystemExit('Approval evidence must contain the user\'s explicit approval message')
    receipt = {
        'at': now(),
        'kind': kind,
        'artifact_hash': artifact_hash,
        'evidence': evidence,
    }
    receipt['id'] = digest_json(receipt)[:20]
    append_jsonl(control / 'approvals.jsonl', receipt)
    return receipt['id']


def validate_verification(media_path: Path, verification_path: Path, *, preview_hash: str | None = None,
                          min_ssim: float | None = None) -> dict[str, Any]:
    verification = read_json(verification_path)
    if verification.get('passed') is not True:
        raise SystemExit('Verification JSON does not report passed: true')
    if verification.get('sha256') != sha256(media_path):
        raise SystemExit('Verification JSON hash does not match media')
    if preview_hash is not None:
        comparison = verification.get('comparison')
        if not isinstance(comparison, dict):
            raise SystemExit('Final verification is missing preview-fidelity comparison')
        if comparison.get('preview_sha256') != preview_hash:
            raise SystemExit('Final verification compared against the wrong preview')
        if min_ssim is not None:
            score = comparison.get('ssim')
            if not isinstance(score, (int, float)) or score < min_ssim:
                raise SystemExit(f'Final visual fidelity is below the configured SSIM threshold: {score}')
    return verification


def init(project: str) -> None:
    root, control, state_path = paths(project)
    if not root.is_dir():
        raise SystemExit(f'Missing project folder: {root}')
    control.mkdir(parents=True, exist_ok=True)
    with project_lock(control):
        if not state_path.exists():
            data = read_json(suite_root() / 'templates' / 'state.template.json')
            data['project_root'] = str(root)
            data['created_at'] = now()
            data['updated_at'] = data['created_at']
            data['history'] = [{'at': data['created_at'], 'phase': 'uninitialized', 'event': 'initialized'}]
            write_json(state_path, data)
        config_path = control / 'config.json'
        if not config_path.exists():
            shutil.copyfile(suite_root() / 'templates' / 'config.template.json', config_path)
    print(state_path)


def sync_clips(project: str) -> None:
    root, control, state_path, data = load(project)
    inventory_path = control / 'clip_inventory.json'
    if not inventory_path.exists():
        raise SystemExit('Missing clip inventory')
    inventory = read_json(inventory_path)
    order = [clip['path'] for clip in inventory.get('clips', [])]
    if not order:
        raise SystemExit('No source clips found')
    fingerprints = {clip['path']: clip.get('fingerprint') for clip in inventory.get('clips', [])}
    with project_lock(control):
        context_was_approved = bool(data['transcript'].get('approved_hash'))
        context_changed = False
        if context_was_approved:
            try:
                guard_context(root, data)
            except SystemExit:
                context_changed = True
        old_order = list(data.get('clip_order', []))
        data['clip_order'] = order
        for clip in order:
            record = data.setdefault('clips', {}).get(clip)
            if not isinstance(record, dict):
                record = fresh_clip_record(fingerprints.get(clip))
                data['clips'][clip] = record
            record['source_fingerprint'] = fingerprints.get(clip)
        for stale in list(data.get('clips', {})):
            if stale not in order:
                del data['clips'][stale]
        if data.get('current_clip') not in order:
            data['current_clip'] = next((clip for clip in order if data['clips'][clip].get('status') != 'complete'), order[0])
        if old_order and old_order != order:
            context_changed = context_was_approved
        if context_changed:
            data['phase'] = 'transcribing'
            data['transcript']['approved_hash'] = None
            data['transcript']['approved_at'] = None
            data['transcript']['approval_receipt_id'] = None
            invalidate_downstream(data)
            event = 'project context changed; downstream approvals invalidated'
        else:
            event = 'clip inventory synchronized'
        save(state_path, data, event)
    print(json.dumps({'clip_order': order, 'current_clip': data['current_clip'], 'invalidated': context_changed}, indent=2))


def begin_transcription(project: str, reason: str) -> None:
    root, control, state_path, data = load(project)
    with project_lock(control):
        data['phase'] = 'transcribing'
        data['transcript']['approved_hash'] = None
        data['transcript']['approved_at'] = None
        data['transcript']['approval_receipt_id'] = None
        invalidate_downstream(data)
        record_context(root, data)
        save(state_path, data, reason)
    print('transcribing')


def await_transcript(project: str) -> None:
    root, control, state_path, data = load(project)
    transcript, _ = project_relative(root, data['transcript']['path'], must_exist=True)
    plan, _ = project_relative(root, data['editing_plan']['path'], must_exist=True)
    with project_lock(control):
        record_context(root, data)
        data['transcript']['hash'] = sha256(transcript)
        data['transcript']['approved_hash'] = None
        data['transcript']['approved_at'] = None
        data['transcript']['approval_receipt_id'] = None
        data['editing_plan']['hash'] = sha256(plan)
        invalidate_downstream(data)
        data['phase'] = 'awaiting_transcript_approval'
        save(state_path, data, 'transcript and provisional plan created; approval required')
    print(data['transcript']['hash'])


def approve_transcript(project: str, evidence: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'awaiting_transcript_approval':
        raise SystemExit('Not awaiting transcript approval')
    guard_context(root, data)
    transcript, _ = project_relative(root, data['transcript']['path'], must_exist=True)
    current = sha256(transcript)
    with project_lock(control):
        if current != data['transcript'].get('hash'):
            data['transcript']['hash'] = current
            data['transcript']['approved_hash'] = None
            invalidate_downstream(data)
            save(state_path, data, 'transcript changed before approval; review required')
            raise SystemExit('Transcript changed; review the current file before approval')
        receipt = record_approval(control, 'transcript', current, evidence)
        data['transcript']['approved_hash'] = current
        data['transcript']['approved_at'] = now()
        data['transcript']['approval_receipt_id'] = receipt
        data['phase'] = 'planning'
        save(state_path, data, 'transcript explicitly approved')
    print(current)


def record_guide(project: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'planning':
        raise SystemExit('Guide can only be recorded during planning')
    guard_context(root, data)
    guard_transcript(root, data)
    guide, _ = project_relative(root, data['guide']['path'], must_exist=True)
    with project_lock(control):
        data['guide']['hash'] = sha256(guide)
        data['phase'] = 'previewing_current_clip'
        save(state_path, data, 'editing guide recorded')
    print(data['guide']['hash'])


def require_story_cut(project: str, plan: str, preview: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'planning':
        raise SystemExit('Story cut must be created after transcript approval and before the visual guide')
    guard_context(root, data)
    guard_transcript(root, data)
    plan_path, plan_relative = safe_output(root, data, plan)
    preview_path, preview_relative = safe_output(root, data, preview)
    with project_lock(control):
        data['story_cut'].update({
            'required': True,
            'plan_path': plan_relative,
            'preview_path': preview_relative,
            'preview_hash': sha256(preview_path),
            'approved_hash': None,
            'approval_receipt_id': None,
        })
        data['phase'] = 'awaiting_story_cut_approval'
        save(state_path, data, 'story-cut rough preview created; approval required')
    print(data['story_cut']['preview_hash'])


def approve_story_cut(project: str, evidence: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'awaiting_story_cut_approval':
        raise SystemExit('Not awaiting story-cut approval')
    guard_context(root, data)
    guard_transcript(root, data)
    preview, _ = safe_output(root, data, data['story_cut']['preview_path'])
    current = sha256(preview)
    with project_lock(control):
        if current != data['story_cut'].get('preview_hash'):
            data['story_cut']['preview_hash'] = current
            data['story_cut']['approved_hash'] = None
            save(state_path, data, 'story-cut preview changed; approval invalidated')
            raise SystemExit('Story-cut preview changed; review it again')
        receipt = record_approval(control, 'story-cut', current, evidence)
        data['story_cut']['approved_hash'] = current
        data['story_cut']['approval_receipt_id'] = receipt
        data['phase'] = 'planning'
        save(state_path, data, 'story-cut preview explicitly approved')
    print(current)


def await_preview(project: str, clip: str, path: str, recipe: str, verification: str) -> None:
    root, control, state_path, data = load(project)
    guard_context(root, data)
    guard_transcript(root, data)
    guard_guide(root, data)
    if data['phase'] != 'previewing_current_clip':
        raise SystemExit('Preview is not allowed in the current phase')
    if clip != data.get('current_clip'):
        raise SystemExit(f'Current clip is {data.get("current_clip")!r}, not {clip!r}')
    preview, relative = safe_output(root, data, path)
    recipe_path, recipe_relative = safe_output(root, data, recipe)
    verification_path, verification_relative = safe_output(root, data, verification)
    recipe_payload = verify_recipe(root, recipe_path)
    if recipe_payload.get('clip') != clip:
        raise SystemExit('Render recipe belongs to a different clip')
    validate_verification(preview, verification_path)
    with project_lock(control):
        record = data['clips'][clip]
        record['preview_version'] = int(record.get('preview_version', 0)) + 1
        record.update({
            'preview_path': relative,
            'preview_hash': sha256(preview),
            'preview_verification_path': verification_relative,
            'recipe_path': recipe_relative,
            'recipe_hash': sha256(recipe_path),
            'recipe_bundle_digest': recipe_payload['bundle_digest'],
            'approved_preview_hash': None,
            'approved_recipe_hash': None,
            'approved_recipe_bundle_digest': None,
            'approved_guide_hash': None,
            'preview_approval_receipt_id': None,
            'status': 'awaiting_preview_approval',
        })
        data['phase'] = 'awaiting_current_preview_approval'
        save(state_path, data, f'preview v{record["preview_version"]} created for {clip}; approval required')
    print(record['preview_hash'])


def approve_preview(project: str, clip: str, evidence: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'awaiting_current_preview_approval':
        raise SystemExit('Not awaiting current-preview approval')
    guard_context(root, data)
    guard_transcript(root, data)
    guard_guide(root, data)
    if clip != data.get('current_clip'):
        raise SystemExit('Approval target is not the current clip')
    record = data['clips'][clip]
    preview, _ = safe_output(root, data, record['preview_path'])
    recipe_path, _ = safe_output(root, data, record['recipe_path'])
    current_preview = sha256(preview)
    recipe_payload = verify_recipe(root, recipe_path)
    current_recipe = sha256(recipe_path)
    with project_lock(control):
        if current_preview != record.get('preview_hash') or current_recipe != record.get('recipe_hash'):
            record['preview_hash'] = current_preview
            record['recipe_hash'] = current_recipe
            record['approved_preview_hash'] = None
            record['approved_recipe_hash'] = None
            record['approved_recipe_bundle_digest'] = None
            record['approved_guide_hash'] = None
            save(state_path, data, 'preview or render recipe changed; approval invalidated')
            raise SystemExit('Preview or render recipe changed; review it again')
        receipt = record_approval(control, 'preview', current_preview, evidence)
        record['approved_preview_hash'] = current_preview
        record['approved_recipe_hash'] = current_recipe
        record['approved_recipe_bundle_digest'] = recipe_payload['bundle_digest']
        record['approved_guide_hash'] = data['guide']['hash']
        record['preview_approval_receipt_id'] = receipt
        record['status'] = 'preview_approved'
        data['phase'] = 'finalizing_current_clip'
        save(state_path, data, f'preview explicitly approved for {clip}')
    print(current_preview)


def mark_final(project: str, clip: str, path: str, verification: str) -> None:
    root, control, state_path, data = load(project)
    guard_context(root, data)
    guard_transcript(root, data)
    guard_guide(root, data)
    if data['phase'] != 'finalizing_current_clip' or clip != data.get('current_clip'):
        raise SystemExit('Current clip is not authorized for finalization')
    record = data['clips'][clip]
    preview, _ = safe_output(root, data, record['preview_path'])
    recipe_path, _ = safe_output(root, data, record['recipe_path'])
    recipe_payload = verify_recipe(root, recipe_path)
    if sha256(preview) != record.get('approved_preview_hash'):
        raise SystemExit('Approved preview hash mismatch')
    if sha256(recipe_path) != record.get('approved_recipe_hash'):
        raise SystemExit('Approved render recipe changed')
    if recipe_payload.get('bundle_digest') != record.get('approved_recipe_bundle_digest'):
        raise SystemExit('Approved Remotion inputs changed after preview approval')
    if record.get('approved_guide_hash') != data['guide']['hash']:
        raise SystemExit('Editing guide changed after preview approval')
    final_path, final_relative = safe_output(root, data, path)
    verification_path, verification_relative = safe_output(root, data, verification)
    config = read_json(root / data['context']['config_path'])
    compare = bool(config.get('verification', {}).get('compare_final_to_preview', True))
    threshold = float(config.get('render', {}).get('fidelity_min_ssim', 0.95))
    validate_verification(
        final_path,
        verification_path,
        preview_hash=record['approved_preview_hash'] if compare else None,
        min_ssim=threshold if compare else None,
    )
    with project_lock(control):
        record.update({
            'final_path': final_relative,
            'final_hash': sha256(final_path),
            'verification_path': verification_relative,
            'status': 'complete',
        })
        remaining = [name for name in data['clip_order'] if data['clips'][name]['status'] != 'complete']
        data['phase'] = 'all_clips_complete' if not remaining else 'current_clip_complete'
        save(state_path, data, f'final verified and recorded for {clip}')
    print(record['final_hash'])


def advance_clip(project: str, evidence: str) -> None:
    root, control, state_path, data = load(project)
    if data['phase'] != 'current_clip_complete':
        raise SystemExit('Cannot advance from the current phase')
    completed = data.get('current_clip')
    artifact_hash = data['clips'][completed].get('final_hash') if completed else 'none'
    with project_lock(control):
        record_approval(control, 'continue', str(artifact_hash), evidence)
        next_clip = next((clip for clip in data['clip_order'] if data['clips'][clip]['status'] != 'complete'), None)
        if next_clip is None:
            data['current_clip'] = None
            data['phase'] = 'all_clips_complete'
        else:
            data['current_clip'] = next_clip
            data['phase'] = 'previewing_current_clip'
        save(state_path, data, 'user explicitly continued to the next incomplete clip')
    print(data['current_clip'])


def approve_merge(project: str, evidence: str) -> None:
    _, control, state_path, data = load(project)
    if data['phase'] != 'all_clips_complete':
        raise SystemExit('All clips must be complete before merge approval')
    finals_digest = digest_json([data['clips'][clip].get('final_hash') for clip in data['clip_order']])
    with project_lock(control):
        receipt = record_approval(control, 'merge', finals_digest, evidence)
        data['merge']['approved'] = True
        data['merge']['approval_receipt_id'] = receipt
        data['phase'] = 'merge_approved'
        save(state_path, data, 'merge explicitly requested')
    print('merge_approved')


def mark_merged(project: str, path: str, verification: str) -> None:
    root, control, state_path, data = load(project)
    guard_context(root, data)
    if data['phase'] not in {'merge_approved', 'merging'} or not data['merge'].get('approved'):
        raise SystemExit('Merge is not approved')
    for clip in data['clip_order']:
        record = data['clips'][clip]
        final, _ = safe_output(root, data, record['final_path'])
        if sha256(final) != record.get('final_hash'):
            raise SystemExit(f'Final changed before merge: {clip}')
    merged, merged_relative = safe_output(root, data, path)
    verification_path, verification_relative = safe_output(root, data, verification)
    validate_verification(merged, verification_path)
    with project_lock(control):
        data['merge'].update({
            'path': merged_relative,
            'hash': sha256(merged),
            'verification_path': verification_relative,
        })
        data['phase'] = 'complete'
        save(state_path, data, 'merged output recorded')
    print(data['merge']['hash'])


def status(project: str) -> None:
    root, _, _, data = load(project)
    warnings: list[str] = []
    if data['transcript'].get('approved_hash'):
        try:
            guard_context(root, data)
        except SystemExit as exc:
            warnings.append(str(exc))
        try:
            guard_transcript(root, data)
        except SystemExit as exc:
            warnings.append(str(exc))
    if data['guide'].get('hash'):
        try:
            guard_guide(root, data)
        except SystemExit as exc:
            warnings.append(str(exc))
    current = data.get('current_clip')
    if current and current in data.get('clips', {}):
        record = data['clips'][current]
        if record.get('approved_recipe_hash'):
            try:
                recipe_path, _ = safe_output(root, data, record['recipe_path'])
                payload = verify_recipe(root, recipe_path)
                if sha256(recipe_path) != record['approved_recipe_hash'] or payload['bundle_digest'] != record['approved_recipe_bundle_digest']:
                    warnings.append('Approved render recipe or Remotion inputs changed')
            except SystemExit as exc:
                warnings.append(str(exc))
    output = dict(data)
    output['warnings'] = warnings
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description='m-edit approval-gated state machine')
    subparsers = parser.add_subparsers(dest='command', required=True)

    for name in ('init', 'sync-clips', 'await-transcript', 'record-guide', 'status'):
        command = subparsers.add_parser(name)
        command.add_argument('--project', required=True)

    command = subparsers.add_parser('begin-transcription')
    command.add_argument('--project', required=True)
    command.add_argument('--reason', default='transcription started or project context refreshed')

    for name in ('approve-transcript', 'approve-story-cut', 'advance-clip', 'approve-merge'):
        command = subparsers.add_parser(name)
        command.add_argument('--project', required=True)
        command.add_argument('--evidence', required=True)

    command = subparsers.add_parser('require-story-cut')
    command.add_argument('--project', required=True)
    command.add_argument('--plan', required=True)
    command.add_argument('--preview', required=True)

    command = subparsers.add_parser('await-preview')
    command.add_argument('--project', required=True)
    command.add_argument('--clip', required=True)
    command.add_argument('--path', required=True)
    command.add_argument('--recipe', required=True)
    command.add_argument('--verification', required=True)

    command = subparsers.add_parser('approve-preview')
    command.add_argument('--project', required=True)
    command.add_argument('--clip', required=True)
    command.add_argument('--evidence', required=True)

    command = subparsers.add_parser('mark-final')
    command.add_argument('--project', required=True)
    command.add_argument('--clip', required=True)
    command.add_argument('--path', required=True)
    command.add_argument('--verification', required=True)

    command = subparsers.add_parser('mark-merged')
    command.add_argument('--project', required=True)
    command.add_argument('--path', required=True)
    command.add_argument('--verification', required=True)

    args = parser.parse_args()
    actions = {
        'init': lambda: init(args.project),
        'sync-clips': lambda: sync_clips(args.project),
        'begin-transcription': lambda: begin_transcription(args.project, args.reason),
        'await-transcript': lambda: await_transcript(args.project),
        'approve-transcript': lambda: approve_transcript(args.project, args.evidence),
        'record-guide': lambda: record_guide(args.project),
        'require-story-cut': lambda: require_story_cut(args.project, args.plan, args.preview),
        'approve-story-cut': lambda: approve_story_cut(args.project, args.evidence),
        'await-preview': lambda: await_preview(args.project, args.clip, args.path, args.recipe, args.verification),
        'approve-preview': lambda: approve_preview(args.project, args.clip, args.evidence),
        'mark-final': lambda: mark_final(args.project, args.clip, args.path, args.verification),
        'advance-clip': lambda: advance_clip(args.project, args.evidence),
        'approve-merge': lambda: approve_merge(args.project, args.evidence),
        'mark-merged': lambda: mark_merged(args.project, args.path, args.verification),
        'status': lambda: status(args.project),
    }
    actions[args.command]()


if __name__ == '__main__':
    main()
