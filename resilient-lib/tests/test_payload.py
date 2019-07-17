import unittest
import json
from resilient_lib.components.function_result import ResultPayload

class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def test_function_result(self):
        pgkname = "requests"
        params = { "param1": "value1",
                    "param2": "value2",
                    "param3": "value3"
                 }
        fr = ResultPayload(pgkname, **params)

        result = { "result1": "value1",
                   "result2": "value2",
                   "result3": "value3"
                 }
        result_dumps = json.dumps(result)

        result = fr.done(True, result)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result['success'])
        self.assertTrue(result['success'])
        self.assertEqual(result['reason'], None)
        self.assertEqual(result['content']["result1"], "value1")
        self.assertEqual(result['raw'], result_dumps)
        self.assertIsNotNone(result.get('metrics'))
        self.assertEqual(result.get('metrics')['package'], pgkname)
        self.assertIsNotNone(result.get('inputs'))
        self.assertEqual(result['inputs']['param1'], 'value1')
