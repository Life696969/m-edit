import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def metadata(skill: str) -> dict:
    text = (ROOT / 'skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
    return yaml.safe_load(text.split('---', 2)[1])


class TriggerDescriptionTests(unittest.TestCase):
    def test_descriptions_cover_distinct_user_intents(self):
        required_terms = {
            'm-edit': ('edit videos', 'captions', 'resume'),
            'm-edit-transcribe': ('transcript', 'timestamped'),
            'm-edit-plan': ('transcript is approved', 'guide'),
            'm-edit-story-cut': ('long-form', 'rough structural cut'),
            'm-edit-preview': ('current clip', 'preview'),
            'm-edit-final': ('preview is explicitly approved', 'final'),
            'm-edit-merge': ('every individual final', 'combine'),
            'm-edit-status': ('awaiting approval', 'resume'),
            'm-edit-doctor': ('failing or uncertain', 'configuration'),
        }
        descriptions = {}
        for skill, terms in required_terms.items():
            description = metadata(skill)['description'].lower()
            descriptions[skill] = description
            for term in terms:
                self.assertIn(term, description, f'{skill} missing trigger term {term!r}')
        self.assertEqual(len(set(descriptions.values())), len(descriptions))

    def test_specialists_do_not_claim_all_video_editing_requests(self):
        for path in (ROOT / 'skills').glob('m-edit-*/SKILL.md'):
            description = metadata(path.parent.name)['description'].lower()
            self.assertNotEqual(description, 'use when editing videos')


if __name__ == '__main__':
    unittest.main()
