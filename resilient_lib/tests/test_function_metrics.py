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
        self.assertIsNotNone(result['version'])
        self.assertIsNotNone(result['host'])
        self.assertIsNotNone(result['execution_time_ms'])
        self.assertIsNotNone(result['timestamp'])

