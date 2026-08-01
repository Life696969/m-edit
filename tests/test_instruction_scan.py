import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / 'shared' / 'scripts' / 'scan_instructions.py'


class InstructionScanTests(unittest.TestCase):
    def test_ancestors_only_nearer_rules_load_last_and_siblings_are_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / '.m-edit-root').write_text('', encoding='utf-8')
            (base / 'AGENTS.md').write_text('global', encoding='utf-8')
            category = base / 'category'
            category.mkdir()
            (category / 'CAPTION_RULES.md').write_text('category', encoding='utf-8')
            project = category / 'project-a'
            project.mkdir()
            (project / 'CLIP_NOTES.md').write_text('local', encoding='utf-8')
            (project / 'transcript.md').write_text('generated', encoding='utf-8')
            sibling = category / 'project-b'
            sibling.mkdir()
            (sibling / 'AGENTS.md').write_text('sibling', encoding='utf-8')

            subprocess.run(['python3', str(SCAN), '--project', str(project)], check=True, capture_output=True, text=True)
            manifest = json.loads((project / '.m-edit' / 'instruction_manifest.json').read_text(encoding='utf-8'))
            paths = [row['path'].replace('\\', '/') for row in manifest['files']]
            self.assertEqual(paths, ['../../AGENTS.md', '../CAPTION_RULES.md', 'CLIP_NOTES.md'])
            self.assertNotIn('transcript.md', paths)
            self.assertFalse(any('project-b' in path for path in paths))

    def test_ancestor_keyword_files_are_off_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / '.m-edit-root').write_text('', encoding='utf-8')
            (base / 'random-video-thoughts.md').write_text('not trusted by default', encoding='utf-8')
            project = base / 'project'
            project.mkdir()
            subprocess.run(['python3', str(SCAN), '--project', str(project)], check=True, capture_output=True, text=True)
            manifest = json.loads((project / '.m-edit' / 'instruction_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['files'], [])

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside_temp:
            base = Path(temporary)
            (base / '.m-edit-root').write_text('', encoding='utf-8')
            project = base / 'project'
            project.mkdir()
            outside = Path(outside_temp) / 'AGENTS.md'
            outside.write_text('outside', encoding='utf-8')
            link = project / 'AGENTS.md'
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest('symlinks unavailable')
            completed = subprocess.run(['python3', str(SCAN), '--project', str(project)], capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)


if __name__ == '__main__':
    unittest.main()
