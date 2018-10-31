import unittest
from resilient_lib.components.resilient_common import build_function_result

class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def test_payload(self):
        result = build_function_result(True, 'no reason', {"a": "a", "b": "b"}, None, None)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result['success'])
        self.assertTrue(result['success'])
        self.assertEqual(result['reason'], 'no reason')
        self.assertEqual(result['content']["a"], "a")
        self.assertIsNone(result.get('metrics'))
        self.assertIsNone(result.get('inputs'))

