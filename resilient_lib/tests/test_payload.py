import unittest
from resilient_lib.components.function_result import FunctionResult

class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def test_function_result(self):
        pgkname = "requests"
        params = { "param1": "value1",
                    "param2": "value2",
                    "param3": "value3"
                 }
        fr = FunctionResult(pgkname, **params)

        result = { "result1": "value1",
                   "result2": "value2",
                   "result3": "value3"
                 }

        result = fr.done(True, None, result)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result['success'])
        self.assertTrue(result['success'])
        self.assertEqual(result['reason'], None)
        self.assertEqual(result['content']["result1"], "value1")
        self.assertIsNotNone(result.get('metrics'))
        self.assertEqual(result.get('metrics')['package'], pgkname)
        self.assertIsNotNone(result.get('inputs'))
        self.assertEqual(result['inputs']['param1'], 'value1')

