import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'shared' / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


state = load_module('m_edit_state_tests', SCRIPTS / 'state.py')
common = load_module('m_edit_common_tests', SCRIPTS / 'common.py')
recipe = load_module('m_edit_recipe_tests', SCRIPTS / 'recipe.py')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name).resolve()
        (self.project / 'clip1.mp4').write_bytes(b'clip-one-source')
        (self.project / 'clip2.mp4').write_bytes(b'clip-two-source')
        (self.project / 'VIDEO_EDITING_RULES.md').write_text('Keep edits clear.\n', encoding='utf-8')
        state.init(str(self.project))
        control = self.project / '.m-edit'
        rule = self.project / 'VIDEO_EDITING_RULES.md'
        rows = [{
            'path': 'VIDEO_EDITING_RULES.md',
            'relative_to_boundary': 'VIDEO_EDITING_RULES.md',
            'ancestor_distance': 0,
            'name_score': 110,
            'sha256': digest(rule),
            'size_bytes': rule.stat().st_size,
        }]
        manifest = {
            'schema_version': 2,
            'project_root': str(self.project),
            'boundary': str(self.project),
            'files': rows,
            'files_digest': common.digest_json(rows),
        }
        (control / 'instruction_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        clips = []
        for name in ('clip1.mp4', 'clip2.mp4'):
            path = self.project / name
            stat = path.stat()
            clips.append({
                'path': name,
                'fingerprint': {
                    'size_bytes': stat.st_size,
                    'mtime_ns': stat.st_mtime_ns,
                    'hash_mode': 'full',
                    'sha256': digest(path),
                },
            })
        inventory = {'schema_version': 2, 'clips': clips}
        (control / 'clip_inventory.json').write_text(json.dumps(inventory), encoding='utf-8')
        state.sync_clips(str(self.project))
        state.begin_transcription(str(self.project), 'test setup')
        (self.project / 'transcript.md').write_text('# Transcript\nhello\n', encoding='utf-8')
        (self.project / 'editing_plan.md').write_text('# Provisional plan\n', encoding='utf-8')

    def tearDown(self):
        self.temporary.cleanup()

    def load_state(self):
        return json.loads((self.project / '.m-edit' / 'state.json').read_text(encoding='utf-8'))

    def approve_transcript(self):
        state.await_transcript(str(self.project))
        state.approve_transcript(str(self.project), 'I reviewed the transcript and approve it.')

    def record_guide(self):
        (self.project / 'video_editing_guide.md').write_text('# Guide\nUse clean captions.\n', encoding='utf-8')
        state.record_guide(str(self.project))

    def make_recipe(self, clip='clip1.mp4', filename='recipe.json') -> Path:
        src = self.project / 'remotion' / 'src'
        src.mkdir(parents=True, exist_ok=True)
        (src / 'Root.tsx').write_text('export const Root = () => null;\n', encoding='utf-8')
        (src / 'captions.json').write_text('[]\n', encoding='utf-8')
        payload = {
            'schema_version': 1,
            'clip': clip,
            'composition_id': 'ClipPreview',
            'entry_point': 'remotion/src/Root.tsx',
            'input_props': None,
            'render_command': 'npx remotion render ClipPreview',
            'files': recipe.collect_files(self.project, [clip, 'remotion/src']),
        }
        payload['bundle_digest'] = recipe.bundle_digest(payload)
        path = self.project / filename
        common.write_json(path, payload)
        return path

    def verification(self, media: Path, filename: str, *, preview: Path | None = None, passed=True, override_hash=None):
        payload = {
            'schema_version': 2,
            'passed': passed,
            'sha256': override_hash or digest(media),
        }
        if preview is not None:
            payload['comparison'] = {
                'preview_sha256': digest(preview),
                'ssim': 1.0,
                'passed': True,
            }
        path = self.project / filename
        path.write_text(json.dumps(payload), encoding='utf-8')
        return path

    def make_preview_and_approve(self, clip='clip1.mp4', filename='preview.mp4', recipe_name='recipe.json'):
        preview = self.project / filename
        preview.write_bytes(f'preview-{clip}'.encode())
        recipe_path = self.make_recipe(clip, recipe_name)
        verification = self.verification(preview, f'{filename}.verification.json')
        state.await_preview(str(self.project), clip, filename, recipe_path.name, verification.name)
        state.approve_preview(str(self.project), clip, 'I reviewed this preview and approve it for final rendering.')
        return preview, recipe_path

    def mark_final(self, clip: str, preview: Path, filename: str):
        final = self.project / filename
        final.write_bytes(preview.read_bytes())
        verification = self.verification(final, f'{filename}.verification.json', preview=preview)
        state.mark_final(str(self.project), clip, filename, verification.name)
        return final

    def test_approval_evidence_is_required(self):
        state.await_transcript(str(self.project))
        with self.assertRaises(SystemExit):
            state.approve_transcript(str(self.project), '')

    def test_transcript_change_blocks_approval(self):
        state.await_transcript(str(self.project))
        (self.project / 'transcript.md').write_text('changed', encoding='utf-8')
        with self.assertRaises(SystemExit):
            state.approve_transcript(str(self.project), 'approved')

    def test_touching_full_hashed_source_without_content_change_does_not_invalidate(self):
        self.approve_transcript()
        self.record_guide()
        path = self.project / 'clip1.mp4'
        os.utime(path, None)
        state.guard_context(self.project, self.load_state())

    def test_source_mutation_blocks_downstream(self):
        self.approve_transcript()
        self.record_guide()
        (self.project / 'clip1.mp4').write_bytes(b'mutated-source')
        with self.assertRaises(SystemExit):
            state.await_preview(str(self.project), 'clip1.mp4', 'missing.mp4', 'missing.json', 'missing-verification.json')

    def test_instruction_mutation_blocks_downstream(self):
        self.approve_transcript()
        self.record_guide()
        (self.project / 'VIDEO_EDITING_RULES.md').write_text('changed rule\n', encoding='utf-8')
        with self.assertRaises(SystemExit):
            state.await_preview(str(self.project), 'clip1.mp4', 'missing.mp4', 'missing.json', 'missing-verification.json')

    def test_only_current_clip_can_be_previewed(self):
        self.approve_transcript()
        self.record_guide()
        preview = self.project / 'preview2.mp4'
        preview.write_bytes(b'preview2')
        recipe_path = self.make_recipe('clip2.mp4', 'recipe2.json')
        verification = self.verification(preview, 'preview2.verification.json')
        with self.assertRaises(SystemExit):
            state.await_preview(str(self.project), 'clip2.mp4', preview.name, recipe_path.name, verification.name)

    def test_path_traversal_is_rejected(self):
        self.approve_transcript()
        self.record_guide()
        outside = self.project.parent / 'outside-preview.mp4'
        outside.write_bytes(b'preview')
        try:
            with self.assertRaises(SystemExit):
                state.await_preview(str(self.project), 'clip1.mp4', '../outside-preview.mp4', 'recipe.json', 'verification.json')
        finally:
            outside.unlink(missing_ok=True)

    def test_preview_mutation_blocks_final(self):
        self.approve_transcript()
        self.record_guide()
        preview, _ = self.make_preview_and_approve()
        preview.write_bytes(b'changed-preview')
        final = self.project / 'final.mp4'
        final.write_bytes(b'changed-preview')
        verification = self.verification(final, 'final.verification.json', preview=preview)
        with self.assertRaises(SystemExit):
            state.mark_final(str(self.project), 'clip1.mp4', final.name, verification.name)

    def test_guide_mutation_blocks_final(self):
        self.approve_transcript()
        self.record_guide()
        preview, _ = self.make_preview_and_approve()
        (self.project / 'video_editing_guide.md').write_text('# changed guide\n', encoding='utf-8')
        final = self.project / 'final.mp4'
        final.write_bytes(preview.read_bytes())
        verification = self.verification(final, 'final.verification.json', preview=preview)
        with self.assertRaises(SystemExit):
            state.mark_final(str(self.project), 'clip1.mp4', final.name, verification.name)

    def test_remotion_code_mutation_blocks_final(self):
        self.approve_transcript()
        self.record_guide()
        preview, _ = self.make_preview_and_approve()
        (self.project / 'remotion' / 'src' / 'Root.tsx').write_text('export const Root = () => 42;\n', encoding='utf-8')
        final = self.project / 'final.mp4'
        final.write_bytes(preview.read_bytes())
        verification = self.verification(final, 'final.verification.json', preview=preview)
        with self.assertRaises(SystemExit):
            state.mark_final(str(self.project), 'clip1.mp4', final.name, verification.name)

    def test_final_requires_preview_comparison(self):
        self.approve_transcript()
        self.record_guide()
        preview, _ = self.make_preview_and_approve()
        final = self.project / 'final.mp4'
        final.write_bytes(preview.read_bytes())
        verification = self.verification(final, 'final.verification.json')
        with self.assertRaises(SystemExit):
            state.mark_final(str(self.project), 'clip1.mp4', final.name, verification.name)

    def test_sequential_completion_and_explicit_merge(self):
        self.approve_transcript()
        self.record_guide()
        preview1, _ = self.make_preview_and_approve()
        self.mark_final('clip1.mp4', preview1, 'final1.mp4')
        self.assertEqual(self.load_state()['phase'], 'current_clip_complete')

        with self.assertRaises(SystemExit):
            state.approve_merge(str(self.project), 'merge now')
        with self.assertRaises(SystemExit):
            state.advance_clip(str(self.project), '')

        state.advance_clip(str(self.project), 'Continue to the next clip.')
        preview2 = self.project / 'preview2.mp4'
        preview2.write_bytes(b'preview-clip2')
        recipe2 = self.make_recipe('clip2.mp4', 'recipe2.json')
        verify2 = self.verification(preview2, 'preview2.verification.json')
        state.await_preview(str(self.project), 'clip2.mp4', preview2.name, recipe2.name, verify2.name)
        state.approve_preview(str(self.project), 'clip2.mp4', 'I approve clip two preview.')
        self.mark_final('clip2.mp4', preview2, 'final2.mp4')
        self.assertEqual(self.load_state()['phase'], 'all_clips_complete')

        state.approve_merge(str(self.project), 'Merge all verified final clips.')
        data = self.load_state()
        self.assertTrue(data['merge']['approved'])
        receipts = (self.project / '.m-edit' / 'approvals.jsonl').read_text(encoding='utf-8').strip().splitlines()
        self.assertGreaterEqual(len(receipts), 5)


if __name__ == '__main__':
    unittest.main()
