import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'bin/m-edit'


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class EndToEndTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([str(CLI), *args], check=True, capture_output=True, text=True)

    def make_video(self, path: Path):
        subprocess.run([
            'ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=24',
            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '1', '-shortest',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(path),
        ], check=True)

    def test_generated_video_completes_one_clip_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / '.m-edit-root').write_text('', encoding='utf-8')
            source = project / 'clip1.mp4'
            self.make_video(source)

            self.cli('init', '--project', str(project))
            self.cli('scan-clips', '--project', str(project))
            self.cli('scan-instructions', '--project', str(project))
            self.cli('sync-clips', '--project', str(project))
            self.cli('begin-transcription', '--project', str(project), '--reason', 'integration test')
            (project / 'transcript.md').write_text('# Transcript\n\nNo speech in generated fixture.\n', encoding='utf-8')
            (project / 'editing_plan.md').write_text('# Plan\n\nPreserve generated fixture.\n', encoding='utf-8')
            self.cli('await-transcript', '--project', str(project))
            self.cli('approve-transcript', '--project', str(project), '--evidence', 'I approve the generated transcript fixture.')
            (project / 'video_editing_guide.md').write_text('# Guide\n\nPass through video and audio.\n', encoding='utf-8')
            self.cli('record-guide', '--project', str(project))

            remotion = project / 'remotion/src'
            remotion.mkdir(parents=True)
            (remotion / 'Root.tsx').write_text('export const Root = () => null;\n', encoding='utf-8')
            (remotion / 'captions.json').write_text('[]\n', encoding='utf-8')
            output = project / 'm-edit-output/project'
            (output / 'previews').mkdir(parents=True)
            (output / 'finals').mkdir(parents=True)
            (output / 'reports').mkdir(parents=True)
            (output / 'recipes').mkdir(parents=True)
            preview = output / 'previews/clip1-preview-v1.mp4'
            shutil.copy2(source, preview)
            recipe = output / 'recipes/clip1-preview-v1.json'
            preview_verification = output / 'reports/clip1-preview-v1-verification.json'
            preview_sheet = output / 'reports/clip1-preview-v1-contact.jpg'
            self.cli(
                'recipe', 'create', '--project', str(project), '--clip', 'clip1.mp4',
                '--composition-id', 'Fixture', '--entry-point', 'remotion/src/Root.tsx',
                '--include', 'remotion/src', '--render-command', 'fixture-copy',
                '--output', recipe.relative_to(project).as_posix(),
            )
            self.cli(
                'verify', '--input', str(preview), '--output', str(preview_verification),
                '--width', '320', '--height', '240', '--require-audio', '--contact-sheet', str(preview_sheet),
            )
            self.cli(
                'await-preview', '--project', str(project), '--clip', 'clip1.mp4',
                '--path', preview.relative_to(project).as_posix(), '--recipe', recipe.relative_to(project).as_posix(),
                '--verification', preview_verification.relative_to(project).as_posix(),
            )
            self.cli(
                'approve-preview', '--project', str(project), '--clip', 'clip1.mp4',
                '--evidence', 'I approve the generated preview fixture.',
            )

            final = output / 'finals/clip1-final.mp4'
            shutil.copy2(preview, final)
            final_verification = output / 'reports/clip1-final-verification.json'
            self.cli(
                'verify', '--input', str(final), '--output', str(final_verification),
                '--compare-preview', str(preview), '--min-ssim', '0.999', '--require-audio',
            )
            self.cli(
                'mark-final', '--project', str(project), '--clip', 'clip1.mp4',
                '--path', final.relative_to(project).as_posix(),
                '--verification', final_verification.relative_to(project).as_posix(),
            )
            status = json.loads(self.cli('status', '--project', str(project)).stdout)
            self.assertEqual(status['phase'], 'all_clips_complete')
            self.assertEqual(status['clips']['clip1.mp4']['status'], 'complete')
            self.assertEqual(status['warnings'], [])


if __name__ == '__main__':
    unittest.main()
