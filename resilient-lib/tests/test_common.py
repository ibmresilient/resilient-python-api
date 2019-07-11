# -*- coding: utf-8 -*-

import os
import sys
import unittest
from resilient_lib.components.resilient_common import str_to_bool, readable_datetime, validate_fields, \
    unescape, clean_html, build_incident_url, build_resilient_url, get_file_attachment, get_file_attachment_name, \
    get_file_attachment_metadata, get_app_config_option, get_function_input, get_all_function_inputs, write_to_tmp_file


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
        test_dict = {"a": "a", "b": "b", "c": ''}

        validate_fields(("a", "b"), test_dict)

        with self.assertRaises(ValueError):
            validate_fields(("c"), test_dict)
            validate_fields(("d"), test_dict)

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
            get_file_attachment_metadata(None, 123)

        with self.assertRaises(ValueError):
            get_file_attachment_metadata(None, None, attachment_id=123)

    def test_get_app_config_option(self):
        app_configs = {
            "config_one": "abc",
            "config_two": "<some placeholder>",
            "config_three": None
        }

        # Test mandatory and exists
        option_name = get_app_config_option(app_configs, "config_one", False)
        self.assertEqual(option_name, "abc")

        # Test mandatory and does not exist
        with self.assertRaisesRegex(ValueError, "'config_four' is mandatory and is not set in app.config file. You must set this value to run this function"):
            option_name = get_app_config_option(app_configs, "config_four", False)

        # Test placeholder
        with self.assertRaisesRegex(ValueError, "'config_two' is mandatory and is not set in app.config file. You must set this value to run this function"):
            option_name = get_app_config_option(app_configs, "config_two", False, "<some placeholder>")

        # Test optional
        option_name = get_app_config_option(app_configs, "config_four", True)
        self.assertEqual(option_name, None)

    def test_get_function_input(self):
        inputs = {
            "bool_input": True,
            "unicode_input": u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ",
            "str_input": "some text",
            "num_input": 123,
            "select_input": {"id": 111, "name": "select choice"},
            "multi_select_input": [{"id": 111, "name": "select choice one"}, {"id": 111, "name": "select choice two"}]
        }

        self.assertEquals(get_function_input(inputs, "bool_input", False), True)
        self.assertEquals(get_function_input(inputs, "unicode_input", False), u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ")
        self.assertEquals(get_function_input(inputs, "num_input", False), 123)
        self.assertEquals(get_function_input(inputs, "select_input", False), "select choice")
        self.assertEquals(get_function_input(inputs, "multi_select_input", False), ["select choice one", "select choice two"])

        # Test mandatory and does not exist
        with self.assertRaisesRegex(ValueError, "'an_input' is a mandatory function input"):
            get_function_input(inputs, "an_input", False)

        # Test optional
        the_input = get_function_input(inputs, "an_input", True)
        self.assertEqual(the_input, None)

    def test_get_all_function_inputs(self):
        inputs = {
            "bool_input": True,
            "unicode_input": u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ",
            "multi_select_input": [{"id": 111, "name": "select choice one"}, {"id": 111, "name": "select choice two"}]
        }

        expected_output = {
            "bool_input": True,
            "unicode_input": u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ",
            "multi_select_input": ["select choice one", "select choice two"]
        }

        self.assertEquals(get_all_function_inputs(inputs), expected_output)

        # Test mandatory inputs
        mandatory_inputs = ["bool_input", "other_input"]

        with self.assertRaisesRegex(ValueError, "Mandatory function input not defined\nRequired field is missing or empty: other_input"):
            get_all_function_inputs(inputs, mandatory_inputs)

    def test_write_to_tmp_file(self):

        data_to_write = bytearray(u" դ ե զ է ը թ ժ ի լ խ ծ կ հ ձ ղ ճ մ յ ն ", encoding="utf-8")

        path_tmp_file, path_tmp_dir = write_to_tmp_file(data_to_write)
        self.assertTrue(os.path.isdir(path_tmp_dir))
        self.assertTrue(os.path.isfile(path_tmp_file))
        self.assertTrue("resilient-lib-tmp-" in path_tmp_file)
