import unittest
from resilient_lib.components.resilient_common import str_to_bool, readable_datetime, validate_fields, \
    unescape, clean_html, build_incident_url, build_resilient_url, get_file_attachment, get_file_attachment_name

class TestFunctionMetrics(unittest.TestCase):
    """ Tests for the attachment_hash function"""

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

        str_ts = readable_datetime(ts*1000, rtn_format='%Y-%m-%d')
        self.assertEqual(str_ts, '2018-09-06')

    def test_validate_fields(self):
        # validate_fields(fieldList, kwargs)
        test_dict = { "a": "a", "b": "b", "c": ''}

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
