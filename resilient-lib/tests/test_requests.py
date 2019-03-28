import copy
import json
import logging
import unittest
import pytest
from parameterized import parameterized
from resilient_lib.components.requests_common import RequestsCommon, get_case_insensitive_key_value, is_payload_in_json
from resilient_lib.components.integration_errors import IntegrationError

class TestFunctionRequests(unittest.TestCase):
    """ Tests for the attachment_hash function

    live tests against endpoints are listed below
    """

    URL_TEST_DATA_RESULTS = "https://api.ipify.org"
    URL_TEST_HTTP_VERBS = "https://postman-echo.com"
    URL_TEST_HTTP_STATUS_CODES = "http://httpstat.us"
    URL_TEST_PROXY = "https://gimmeproxy.com/api/getProxy"

    #rc.execute_call(verb, url, payload, log=None, basicauth=None, verify_flag=True, headers=None,
    #            proxies=None, timeout=None, resp_type=json, callback=None):
    LOG = logging.getLogger(__name__)

    def test_resilient_common_proxies(self):
        rc = RequestsCommon()
        self.assertIsNone(rc.get_proxies())

        integrations = { }

        rc = RequestsCommon(opts=integrations)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { } }
        rc = RequestsCommon(integrations, None)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { "https_proxy": "abc" } }
        rc = RequestsCommon(function_opts=None, opts=integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertIsNone(proxies['http'])

        integrations = { "integrations": { "https_proxy": "abc", 'http_proxy': 'def' } }
        rc = RequestsCommon(integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertEqual("def", proxies['http'])
        

    def test_resp_types(self):
        IPIFY = TestFunctionRequests.URL_TEST_DATA_RESULTS

        rc = RequestsCommon(None, None)

        # J S O N
        json_result = rc.execute_call("get", "{}?format=json".format(IPIFY), None)

        try:
            json.dumps(json_result)
        except (TypeError, OverflowError):
            self.fail("result is not json")

        # T E X T
        text_result = rc.execute_call("get", "{}?format=text".format(IPIFY), None, resp_type='text')
        self.assertIsNotNone(text_result)

        # B Y T E S
        bytes_result = rc.execute_call("get", "{}?format=text".format(IPIFY), None, resp_type='bytes')
        self.assertIsNotNone(bytes_result)
        self.assertTrue(isinstance(bytes_result, bytes))


    def test_verbs(self):
        URL = TestFunctionRequests.URL_TEST_HTTP_VERBS

        headers = {
            "Content-type": "application/json; charset=UTF-8"
        }

        payload = {
            'title': 'foo',
            'body': 'bar',
            'userId': 1
        }

        rc = RequestsCommon(None, None)


        # P O S T
        # test json argument without headers
        resp = rc.execute_call("post", "/".join((URL, "post")), payload, log=TestFunctionRequests.LOG)
        print (resp)
        self.assertEqual(resp['json'].get("body"), "bar")

        # test json argument with headers
        resp = rc.execute_call("post", "/".join((URL, "post")), payload, headers=headers, log=TestFunctionRequests.LOG)
        print (resp)
        self.assertEqual(resp['json'].get("body"), "bar")

        # test data argument
        headers_data = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        resp = rc.execute_call("post", "/".join((URL, "post")), payload, headers=headers_data, log=TestFunctionRequests.LOG)
        print (resp)
        self.assertEqual(resp['json'].get("body"), "bar")


        # G E T
        resp = rc.execute_call("get", "/".join((URL, "get")), payload, log=TestFunctionRequests.LOG)
        self.assertTrue(resp['args'].get("userId"))
        self.assertEqual(resp['args'].get("userId"), '1')


        # P U T
        resp = rc.execute_call("put", "/".join((URL, "put")), payload, headers=headers, log=TestFunctionRequests.LOG)
        TestFunctionRequests.LOG.info(resp)
        self.assertTrue(resp['args'].get("title"))
        self.assertEqual(resp['args'].get("title"), 'foo')


        # P A T C H
        patch = {
            'title': 'patch'
        }

        resp = rc.execute_call("patch", "/".join((URL, "patch")), patch, headers=headers, log=TestFunctionRequests.LOG)
        print ("resp {}".format(resp))
        self.assertTrue(resp['args'].get("title"))
        self.assertEqual(resp['args'].get("title"), 'patch')

        # D E L E T E
        DEL_URL = "/".join((URL, "delete"))
        resp = rc.execute_call("delete", DEL_URL, None, log=TestFunctionRequests.LOG)
        self.assertEqual(resp.get("url"), DEL_URL)

        # bad verb
        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("bad", URL, None, log=TestFunctionRequests.LOG)

    def test_statuscode(self):
        URL = TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES

        rc = RequestsCommon(None, None)

        resp = rc.execute_call("get", "/".join((URL, "200")), None, resp_type='text')

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", "/".join((URL, "300")), None, resp_type='text')

    def test_statuscode(self):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "300"))

        def callback(resp):
            if resp.status_code != 300:
                raise ValueError(resp.status_code)

        rc = RequestsCommon(None, None)

        resp = rc.execute_call("get", URL, None, resp_type='text', callback=callback)

    def test_timeout(self):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "200?sleep=30000"))

        rc = RequestsCommon(None, None)

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", URL, None, resp_type='text', timeout=10)


    def test_basicauth(self):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "basic-auth"))
        basicauth = ("postman", "password")

        rc = RequestsCommon(None, None)

        resp = rc.execute_call("get", URL, None, basicauth=basicauth)
        self.assertTrue(resp.get("authenticated"))


    def test_proxy_override(self):
        rc = RequestsCommon(None, None)
        proxies = rc.get_proxies()
        self.assertIsNone(proxies)

        # test only integration proxies
        integrations_xyz =  {
            "integrations": {
                'http_proxy': "http://xyz.com",
                'https_proxy': "https://xyz.com"
            }
        }

        function_proxy_none =  {
            'http_proxy': None,
            'https_proxy': None
        }

        rc = RequestsCommon(integrations_xyz)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://xyz.com")
        self.assertEqual(proxies['https'], "https://xyz.com")

        rc = RequestsCommon(integrations_xyz, function_proxy_none)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://xyz.com")
        self.assertEqual(proxies['https'], "https://xyz.com")

        # test only function proxies
        integrations_none =  {
            "integrations": {
                'http_proxy': None,
                'https_proxy': None
            }
        }

        function_proxy_abc =  {
            'http_proxy': "http://abc.com",
            'https_proxy': "https://abc.com"
        }

        rc = RequestsCommon(function_opts=function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")

        rc = RequestsCommon(integrations_none, function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")


        # test integration and function proxies (override)
        rc = RequestsCommon(integrations_xyz, function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")


    #@pytest.mark.skip(reason="may be over the limit")
    def test_proxy(self):
        rc = RequestsCommon()

        proxy_url = TestFunctionRequests.URL_TEST_PROXY
        proxy_result = rc.execute_call("get", proxy_url, None)

        proxies = {
            'http': proxy_result['curl'] if proxy_result['protocol'] == 'http' else None,
            'https': proxy_result['curl'] if proxy_result['protocol'] == 'https' else None
        }

        URL = "?".join((TestFunctionRequests.URL_TEST_DATA_RESULTS, "format=json"))

        # J S O N
        json_result = rc.execute_call("get", URL, None, proxies=proxies)

        self.assertTrue(json_result.get("ip"))

        integrations =  { "integrations": {
            'http_proxy': proxy_result['curl'] if proxy_result['protocol'] == 'http' else None,
            'https_proxy': proxy_result['curl'] if proxy_result['protocol'] == 'https' else None
        }
        }

        rc = RequestsCommon(opts=integrations)
        json_result = rc.execute_call("get", URL, None)
        self.assertTrue(json_result.get("ip"))


    def test_headers(self):
        # G E T with headers
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "my-sample-header": "my header"
        }
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "headers"))

        rc = RequestsCommon()

        json_result = rc.execute_call("get", URL, None, headers=headers)
        self.assertEqual(json_result['headers'].get("my-sample-header"), "my header")


    @parameterized.expand([
        [None, True],
        ["application/json", True],
        ["application/json; charset=UTF-8", True],
        ["charset=UTF-8; application/json", True],
        ["application/x-www-form-urlencoded", False]
    ])
    def test_is_payload_in_json(self, content_type, result):

        payload_in_json = is_payload_in_json(content_type)

        self.assertEqual(payload_in_json, result)


    @parameterized.expand([
        [None, None],
        [{"Content-Type": "mock_type"}, "mock_type"],
        [{"my-sample-header": "my header"}, None]
    ])
    def test_get_case_insensitive_key_value(self, dictionary, result):

        value = get_case_insensitive_key_value(dictionary, "content-type")

        self.assertEqual(value, result)
