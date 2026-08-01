#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import read_json
from validate_config import validate


def version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip().split('\n')[0]


def main() -> None:
    parser = argparse.ArgumentParser(description='Check whether a project is ready for m-edit.')
    parser.add_argument('--project', required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str, required: bool = True) -> None:
        checks.append({'name': name, 'passed': passed, 'required': required, 'detail': detail})

    add('project-folder', root.is_dir(), str(root))
    add('python', sys.version_info >= (3, 10), sys.version.split()[0])
    for tool, command in (
        ('ffmpeg', ['ffmpeg', '-version']),
        ('ffprobe', ['ffprobe', '-version']),
        ('node', ['node', '--version']),
        ('npm', ['npm', '--version']),
        ('npx', ['npx', '--version']),
    ):
        value = version(command)
        add(tool, value is not None, value or 'not found')

    config_path = root / '.m-edit' / 'config.json'
    if config_path.exists():
        try:
            config = read_json(config_path)
            errors = validate(config)
            add('config', not errors, '; '.join(errors) if errors else str(config_path))
        except SystemExit as exc:
            add('config', False, str(exc))
    else:
        add('config', False, 'run m-edit initialization first')

    package_json = root / 'package.json'
    if package_json.exists():
        try:
            package = read_json(package_json)
            dependencies = {**package.get('dependencies', {}), **package.get('devDependencies', {})}
            remotion = dependencies.get('remotion') or dependencies.get('@remotion/cli')
            add('remotion-project', bool(remotion), f'package version: {remotion}' if remotion else 'package.json has no Remotion dependency')
        except SystemExit as exc:
            add('remotion-project', False, str(exc))
    else:
        add('remotion-project', False, 'no package.json; permission is required before scaffolding', required=False)

    providers = {
        'existing captions': True,
        'openai-whisper CLI': bool(shutil.which('whisper')),
        'faster-whisper Python': importlib.util.find_spec('faster_whisper') is not None,
        'whisper.cpp CLI': bool(shutil.which('whisper-cli') or shutil.which('main')),
        'host-agent transcription': True,
    }
    add('transcription-provider', any(providers.values()), json.dumps(providers, sort_keys=True), required=False)

    writable_target = root / '.m-edit-doctor-write-test'
    try:
        writable_target.write_text('ok', encoding='utf-8')
        writable_target.unlink()
        add('project-writable', True, 'write test passed')
    except OSError as exc:
        add('project-writable', False, str(exc))

    required_failed = [check for check in checks if check['required'] and not check['passed']]
    payload = {'passed': not required_failed, 'project': str(root), 'checks': checks}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for check in checks:
            marker = 'PASS' if check['passed'] else ('WARN' if not check['required'] else 'FAIL')
            print(f'[{marker}] {check["name"]}: {check["detail"]}')
        print('READY' if payload['passed'] else 'NOT READY')
    if required_failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
