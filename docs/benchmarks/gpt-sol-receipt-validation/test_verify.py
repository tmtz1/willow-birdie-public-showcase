import importlib.util
from pathlib import Path
import unittest


class HarnessTests(unittest.TestCase):
    def test_expected_baseline_does_not_hide_errors_or_skips(self):
        path = Path(__file__).with_name('verify.py')
        self.assertTrue(path.exists(), 'Explicit baseline verification harness is missing')
        spec = importlib.util.spec_from_file_location('verify', path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        good = {'run': 30, 'failures': 19, 'errors': 0, 'skipped': 0}
        self.assertTrue(module.matches(good, 30, 19))
        for field in good:
            bad = dict(good)
            bad[field] += 1
            self.assertFalse(module.matches(bad, 30, 19), field)
