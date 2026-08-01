import copy
import importlib.util
import json
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'shared/scripts/validate_config.py'
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location('validate_config_tests', SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'shared/templates/config.template.json').read_text(encoding='utf-8'))

    def test_default_config_is_valid(self):
        self.assertEqual(module.validate(self.config), [])

    def test_fixed_gates_cannot_be_disabled(self):
        for field in module.REQUIRED_TRUE:
            with self.subTest(field=field):
                config = copy.deepcopy(self.config)
                config['workflow'][field] = False
                errors = module.validate(config)
                self.assertTrue(any(field in error for error in errors))

    def test_output_path_must_stay_relative(self):
        config = copy.deepcopy(self.config)
        config['output_root'] = '../outside'
        self.assertTrue(module.validate(config))


if __name__ == '__main__':
    unittest.main()
