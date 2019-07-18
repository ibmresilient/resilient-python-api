# -*- coding: utf-8 -*-

import os
import sys
import unittest
from resilient_lib.components.resilient_common import str_to_bool, readable_datetime, validate_fields, \
    unescape, clean_html, build_incident_url, build_resilient_url, get_file_attachment, get_file_attachment_name, \
    get_file_attachment_metadata, write_to_tmp_file


class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    def setUp(self):
        # assertRaisesRegexp renamed to assertRaisesRegex in PY3.2
        if sys.version_info < (3, 2):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_str_to_bool(self):
        self.assertTrue(str_to_bool('True'))
        self.assertTrue(str_to_bool('true'))
        self.assertTrue(str_to_bool('YES'))
        self.assertFalse(str_to_bool('truex'))
        self.assertTrue(str_to_bool(1))
        self.assertFalse(str_to_bool(0))
        self.assertFalse(str_to_bool('0'))

    def test_readable_datetime(self):
        # readable_datetime(timestamp, milliseconds=True, str_format='%Y-%m-%dT%H:%M:%SZ'):

        ts = 1536194194
        str_ts = readable_datetime(ts, milliseconds=False)
        self.assertEqual(str_ts, '2018-09-06T00:36:34Z')

        str_ts = readable_datetime(ts * 1000, rtn_format='%Y-%m-%d')
        self.assertEqual(str_ts, '2018-09-06')

    def test_validate_fields(self):
        # validate_fields(fieldList, kwargs)

        inputs = {
            "bool_input_true": True,
            "bool_input_false": False,
            "unicode_input": u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ",
            "str_input": "some text",
            "num_input": 123,
            "select_input": {"id": 111, "name": "select choice"},
            "multi_select_input": [{"id": 111, "name": "select choice one"}, {"id": 111, "name": "select choice two"}],
            "empty_input": ''
        }

        mandatory_fields = [
            {"name": "str_input", "placeholder": "some text"}
        ]

        expected_output = {
            "bool_input_true": True,
            "bool_input_false": False,
            "unicode_input": u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ",
            "str_input": "some text",
            "num_input": 123,
            "select_input": "select choice",
            "multi_select_input": ["select choice one", "select choice two"],
            "empty_input": ''
        }

        # Test its runs as expected
        validate_fields(("bool_input_true", "unicode_input"), inputs)

        with self.assertRaisesRegex(ValueError, "'field_list' must be of type list/tuple"):
            validate_fields({}, inputs)

        # Test mandatory fields missing
        with self.assertRaisesRegex(ValueError, "'cx' is mandatory and is not set. You must set this value to run this function"):
            validate_fields(("cx"), inputs)

        # Test mandatory field is empty string
        with self.assertRaisesRegex(ValueError, "'empty_input' is mandatory and is not set. You must set this value to run this function"):
            validate_fields(("empty_input"), inputs)

        # Test no mandatory fields
        self.assertEquals(validate_fields([], inputs), expected_output)

        # Test getting single input from returned dict
        self.assertEquals(validate_fields(("bool_input_true"), inputs).get("bool_input_true"), True)
        self.assertEquals(validate_fields([], inputs).get("bool_input_true"), True)

        # Test getting value defined as False
        self.assertEquals(validate_fields(["bool_input_false"], inputs).get("bool_input_false"), False)

        # Test select + multi-select type fields
        self.assertEquals(validate_fields(["select_input"], inputs).get("select_input"), "select choice")
        self.assertEquals(validate_fields([], inputs).get("multi_select_input"), ["select choice one", "select choice two"])

        # Test placeholder
        with self.assertRaisesRegex(ValueError, "'str_input' is mandatory and still has its placeholder value of 'some text'. You must set this value correctly to run this function"):
            validate_fields(mandatory_fields, inputs)

    def test_unescape(self):
        # unescape(data)
        test_data = "&lt;-&gt;"
        self.assertEqual(unescape(test_data), '<->')

        self.assertEqual(unescape("&ab;xx"), '&ab;xx')
        self.assertIsNone(unescape(None))

    def test_clean_html(self):
        # clean_html(htmlFragment)
        self.assertEqual(clean_html("<div>abc</div>"), "abc")
        self.assertEqual(clean_html("<div><ul><li>abc</li><li>def</li></ul></div>"), "abc def")
        self.assertEqual(clean_html("abc"), "abc")
        self.assertIsNone(clean_html(None))

    def test_build_incident_url(self):
        url = build_incident_url(build_resilient_url("https://localhost", 8443), 12345)
        self.assertEqual(url, "https://localhost:8443/#incidents/12345")

        url = build_incident_url(build_resilient_url("localhost", 8443), 12345)
        self.assertEqual(url, "https://localhost:8443/#incidents/12345")

    def test_file_attachment(self):
        with self.assertRaises(ValueError):
            get_file_attachment(None, 123)

        with self.assertRaises(ValueError):
            get_file_attachment(None, None, attachment_id=123)

    def test_file_attachment_name(self):
        with self.assertRaises(ValueError):
            get_file_attachment_name(None, 123)

        with self.assertRaises(ValueError):
            get_file_attachment_name(None, None, attachment_id=123)

    def test_get_file_attachment_metadata(self):
        with self.assertRaises(ValueError):
            get_file_attachment_metadata(res_client=None, incident_id=123)

        with self.assertRaises(ValueError):
            get_file_attachment_metadata(res_client=None, incident_id=None, attachment_id=123)

    def test_write_to_tmp_file(self):

        data_to_write = bytearray(u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ", encoding="utf-8")

        path_tmp_file, path_tmp_dir = write_to_tmp_file(data_to_write)

        # Test works as expected
        self.assertTrue(os.path.isdir(path_tmp_dir))
        self.assertTrue(os.path.isfile(path_tmp_file))
        self.assertTrue("resilient-lib-tmp-" in path_tmp_file)

        # Test path does not exist
        with self.assertRaisesRegex(IOError, "Path does not exist:"):
            write_to_tmp_file(data_to_write, path_tmp_dir="xxxx")
