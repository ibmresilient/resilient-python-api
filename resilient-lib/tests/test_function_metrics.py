import unittest
from resilient_lib.components.function_metrics import FunctionMetrics


class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def test_parameters(self):
        fm = FunctionMetrics("requests")
        result = fm.finish()

        self.assertIsNotNone(result)
        self.assertIsNotNone(result['package'])
        self.assertEqual(result['package'], 'requests')
        self.assertIsNotNone(result['package_version'])
        self.assertIsNotNone(result['host'])
        self.assertIsNotNone(result['execution_time_ms'])
        self.assertIsNotNone(result['timestamp'])

    def test_bad_pkg(self):
        fm = FunctionMetrics("missing")
        result = fm.finish()

        self.assertIsNotNone(result)
        self.assertIsNotNone(result['package'])
        self.assertEqual(result['package'], 'unknown')
        self.assertEqual(result['package_version'], 'unknown')
        self.assertIsNotNone(result['host'])
        self.assertIsNotNone(result['execution_time_ms'])
        self.assertIsNotNone(result['timestamp'])

