import json
import logging
import os
import time
import unittest

import pytest
import requests
import requests_mock
from parameterized import parameterized
from resilient_lib import (IntegrationError, RequestsCommon,
                           RequestsCommonWithoutSession)
from resilient_lib.components.requests_common import (
    get_case_insensitive_key_value, is_payload_in_json)
from retry.api import retry_call
from six import PY2
from tests.shared_mock_data import mock_paths

# USE THIS TO TEST BOTH VERSIONS OF REQUESTSCOMMON
# Ex:
# @parameterized.expand(REQUESTS_COMMON_CLASSES)
# def test_x(self, RCObjectType):
#    ...
REQUESTS_COMMON_CLASSES = [[RequestsCommon], [RequestsCommonWithoutSession]]
RETRY_TRIES_COUNT = 3
RETRY_DELAY = 2

class TestFunctionRequests(unittest.TestCase):
    """ Tests for the attachment_hash function

    live tests against endpoints are listed below
    """

    URL_TEST_DATA_RESULTS = "https://api.ipify.org"
    URL_TEST_HTTP_VERBS = "https://postman-echo.com"
    URL_TEST_HTTP_STATUS_CODES = "http://httpstat.us"
    URL_TEST_PROXY = "https://gimmeproxy.com/api/getProxy"

    LOG = logging.getLogger(__name__)

    @staticmethod
    def retry_function(f, *fargs, **fkwargs):
        """
        FOR ANY FUTURE DEVS HERE: please use this ``retry_function`` to wrap any live RequestsCommon.execute
        calls in retry logic. The goal is to avoid any live tests that fail with server errors.
        See SOARAPPS-7122 for details.
        """
        return retry_call(f=f, fargs=fargs, fkwargs=fkwargs, exceptions=(IntegrationError), tries=RETRY_TRIES_COUNT, delay=RETRY_DELAY)

    @pytest.fixture(autouse=True)
    def init_caplog_fixture(self, caplog):
        self.caplog = caplog

    def test_retry_helper_is_working(self):
        self.caplog.clear() # clear caplog
        # just to test that the above retry helper method is working properly
        rc = RequestsCommon()

        with pytest.raises(IntegrationError):
            self.retry_function(rc.execute, "GET", "https://postman-echo.com/status/404")

        assert self.caplog.text.count("retrying in") == (RETRY_TRIES_COUNT-1)

        self.caplog.clear() # clear caplog


    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_resilient_common_proxies(self, RCObjectType):
        rc = RCObjectType()
        self.assertIsNone(rc.get_proxies())

        integrations = { }

        rc = RCObjectType(opts=integrations)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { } }
        rc = RCObjectType(integrations, None)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { "https_proxy": "abc" } }
        rc = RCObjectType(function_opts=None, opts=integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertIsNone(proxies['http'])

        integrations = { "integrations": { "https_proxy": "abc", 'http_proxy': 'def' } }
        rc = RCObjectType(integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertEqual("def", proxies['http'])

        os.environ["HTTP_PROXY"] = "https://mock.example.com:3128"
        integrations = { "integrations": { "https_proxy": "abc", 'http_proxy': 'def' } }
        rc = RCObjectType(integrations)
        proxies = rc.get_proxies()
        os.environ["HTTP_PROXY"] = ""
        self.assertEqual(None, proxies)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_timeout_overrides(self, RCObjectType):
        # test default timeout
        integrations = { "integrations": { } }
        rc = RCObjectType(integrations, None)
        self.assertEqual(rc.get_timeout(), 30)

        # test global setting
        integrations_timeout = { "integrations": { "timeout": "35" } }
        rc = RequestsCommon(integrations_timeout, None)
        self.assertEqual(rc.get_timeout(), 35)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_timeout_failure(self, RCObjectType):
        # test timeout
        integrations_twenty = { "integrations": { "timeout": "1" } }
        rc = RCObjectType(integrations_twenty, None)
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "delay", "10"))

        with self.assertRaises(IntegrationError):
            self.retry_function(rc.execute_call_v2, "get", url)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_timeout_success(self, RCObjectType):
        integrations_fourty = { "integrations": { "timeout": "5" } }
        rc = RCObjectType(integrations_fourty, None)
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "delay", "1"))
        resp = self.retry_function(rc.execute_call_v2, "get", url)
        assert resp.json() == {"delay": "1"}

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_timeout_section_value(self, RCObjectType):
        # test section override of a global setting
        integrations_fourty = { "integrations": { "timeout": 40 } }
        integration_section = { "timeout": 50 }
        rc = RCObjectType(integrations_fourty, integration_section)
        self.assertEqual(rc.get_timeout(), 50)

    @unittest.skip(reason="https://api.ipify.org/ is currently unavailable")
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

    @unittest.skip(reason="https://api.ipify.org/ is currently unavailable")
    def test_v2_resp_type(self):
        IPIFY = TestFunctionRequests.URL_TEST_DATA_RESULTS

        rc = RequestsCommon(None, None)

        # R E S P O N S E  Object
        response = self.retry_function(rc.execute_call_v2, "get", "{}?format=json".format(IPIFY))

        self.assertTrue(isinstance(response, requests.models.Response))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_verbs(self, RCObjectType):
        URL = TestFunctionRequests.URL_TEST_HTTP_VERBS

        headers = {
            "Content-type": "application/json; charset=UTF-8"
        }

        payload = {
            'title': 'foo',
            'body': 'bar',
            'userId': 1
        }

        rc = RCObjectType(None, None)


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

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_verbs_v2(self, RCObjectType):
        URL = TestFunctionRequests.URL_TEST_HTTP_VERBS

        headers = {
            "Content-type": "application/json; charset=UTF-8"
        }

        payload = {
            'title': 'foo',
            'body': 'bar',
            'userId': 1
        }

        rc = RCObjectType(None, None)

        # P O S T
        # test json argument without headers
        resp = self.retry_function(rc.execute, "post", "/".join((URL, "post")), json=payload)
        print (resp.json())
        self.assertEqual(resp.json()["json"].get("body"), "bar")

        # test json argument with headers
        resp = self.retry_function(rc.execute_call_v2, "post", "/".join((URL, "post")), json=payload, headers=headers)
        print (resp.json())
        self.assertEqual(resp.json()['json'].get("body"), "bar")

        # test data argument
        headers_data = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        resp = self.retry_function(rc.execute, "post", "/".join((URL, "post")), data=payload, headers=headers_data)
        print (resp.json())
        self.assertEqual(resp.json()['json'].get("body"), "bar")

        # G E T
        resp = self.retry_function(rc.execute_call_v2, "get", "/".join((URL, "get")), params=payload)
        self.assertTrue(resp.json()['args'].get("userId"))
        self.assertEqual(resp.json()['args'].get("userId"), '1')

        # P U T
        # With params
        resp = self.retry_function(rc.execute, "put", "/".join((URL, "put")), params=payload, headers=headers)
        TestFunctionRequests.LOG.info(resp)
        self.assertTrue(resp.json()['args'].get("title"))
        self.assertEqual(resp.json()['args'].get("title"), 'foo')

        # With json body
        resp = self.retry_function(rc.execute_call_v2, "put", "/".join((URL, "put")), json=payload, headers=headers)
        TestFunctionRequests.LOG.info(resp)
        self.assertTrue(resp.json()['json'].get("title"))
        self.assertEqual(resp.json()['json'].get("title"), 'foo')

        # P A T C H
        patch = {
            'title': 'patch'
        }
        # With params
        resp = self.retry_function(rc.execute_call_v2, "patch", "/".join((URL, "patch")), params=patch, headers=headers)
        print ("resp {}".format(resp.json()))
        self.assertTrue(resp.json()['args'].get("title"))
        self.assertEqual(resp.json()['args'].get("title"), 'patch')

        # With json body
        resp = self.retry_function(rc.execute_call_v2, "patch", "/".join((URL, "patch")), json=patch, headers=headers)
        print ("resp {}".format(resp.json()))
        self.assertTrue(resp.json()['json'].get("title"))
        self.assertEqual(resp.json()['json'].get("title"), 'patch')

        # D E L E T E
        DEL_URL = "/".join((URL, "delete"))
        resp = self.retry_function(rc.execute_call_v2, "delete", DEL_URL)
        self.assertEqual(resp.json().get("url"), DEL_URL)

        # bad verb
        with self.assertRaises(IntegrationError):
            resp = self.retry_function(rc.execute_call_v2, "bad", URL)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_statuscode(self, RCObjectType):
        URL = TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES

        rc = RCObjectType(None, None)

        resp = rc.execute_call("get", "/".join((URL, "200")), None, resp_type='text')

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", "/".join((URL, "300")), None, resp_type='text')

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_statuscode_v2(self, RCObjectType):
        URL = TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES

        rc = RCObjectType(None, None)

        resp = self.retry_function(rc.execute_call_v2, "get", "/".join((URL, "200")))

        with self.assertRaises(IntegrationError):
            resp = self.retry_function(rc.execute_call_v2, "get", "/".join((URL, "400")))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_statuscode_callback(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "300"))

        def callback(resp):
            if resp.status_code != 300:
                raise ValueError(resp.status_code)

        rc = RCObjectType(None, None)

        resp = rc.execute_call("get", URL, None, resp_type='text', callback=callback)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_statuscode_callback_v2(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "300"))

        def callback(resp):
            if resp.status_code != 300:
                raise ValueError(resp.status_code)

        rc = RCObjectType(None, None)

        resp = self.retry_function(rc.execute_call_v2, "get", URL, callback=callback)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_timeout(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "200?sleep=30000"))

        rc = RCObjectType(None, None)

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", URL, None, resp_type='text', timeout=2)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_timeout_v2(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_STATUS_CODES, "200?sleep=30000"))

        rc = RCObjectType(None, None)

        with self.assertRaises(IntegrationError):
            resp = self.retry_function(rc.execute_call_v2, "get", URL, timeout=2)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_basicauth(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "basic-auth"))
        basicauth = ("postman", "password")

        rc = RCObjectType(None, None)

        resp = rc.execute_call("get", URL, None, basicauth=basicauth)
        self.assertTrue(resp.get("authenticated"))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_basicauth_v2(self, RCObjectType):
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "basic-auth"))
        basicauth = ("postman", "password")

        rc = RCObjectType(None, None)

        resp = self.retry_function(rc.execute_call_v2, "get", URL, auth=basicauth)
        self.assertTrue(resp.json().get("authenticated"))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_proxy_override(self, RCObjectType):
        rc = RCObjectType(None, None)
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

        rc = RCObjectType(integrations_xyz)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://xyz.com")
        self.assertEqual(proxies['https'], "https://xyz.com")

        rc = RCObjectType(integrations_xyz, function_proxy_none)
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

        rc = RCObjectType(function_opts=function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")

        rc = RCObjectType(integrations_none, function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")


        # test integration and function proxies (override)
        rc = RCObjectType(integrations_xyz, function_proxy_abc)
        proxies = rc.get_proxies()
        self.assertEqual(proxies['http'], "http://abc.com")
        self.assertEqual(proxies['https'], "https://abc.com")

    @unittest.skip(reason="may be over the limit")
    def test_proxy(self):
        rc = RequestsCommon()

        proxy_url = self.URL_TEST_PROXY
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

    @unittest.skip(reason="may be over the limit")
    def test_proxy_v2(self):
        rc = RequestsCommon()

        proxy_url = TestFunctionRequests.URL_TEST_PROXY
        proxy_result = self.retry_function(rc.execute_call_v2, "get", proxy_url)
        proxy_result_json = proxy_result.json()

        proxies = {
            'http': proxy_result_json['curl'] if proxy_result_json['protocol'] == 'http' else None,
            'https': proxy_result_json['curl'] if proxy_result_json['protocol'] == 'https' else None
        }

        URL = "?".join((TestFunctionRequests.URL_TEST_DATA_RESULTS, "format=json"))

        # J S O N
        response = self.retry_function(rc.execute_call_v2, "get", URL, proxies=proxies)
        json_result = response.json()

        self.assertTrue(json_result.get("ip"))

        integrations =  { "integrations": {
            'http_proxy': proxy_result_json['curl'] if proxy_result_json['protocol'] == 'http' else None,
            'https_proxy': proxy_result_json['curl'] if proxy_result_json['protocol'] == 'https' else None
        }
        }

        rc = RequestsCommon(opts=integrations)
        response = self.retry_function(rc.execute_call_v2, "get", URL)
        json_result = response.json()
        self.assertTrue(json_result.get("ip"))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_headers(self, RCObjectType):
        # G E T with headers
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "my-sample-header": "my header"
        }
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "headers"))

        rc = RCObjectType()

        json_result = rc.execute_call("get", URL, None, headers=headers)
        self.assertEqual(json_result['headers'].get("my-sample-header"), "my header")

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.livetest
    def test_headers_v2(self, RCObjectType):
        # G E T with headers
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "my-sample-header": "my header"
        }
        URL = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "headers"))

        rc = RCObjectType()

        json_result = self.retry_function(rc.execute_call_v2, "get", URL, headers=headers)
        self.assertEqual(json_result.json()['headers'].get("my-sample-header"), "my header")


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

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_timeout_override(self, RCObjectType):
        rc = RCObjectType(None, None)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 30) # default in get_timeout()

        # test only integration proxies
        integrations_60 =  {
            "integrations": {
                'timeout': "60"
            }
        }

        function_timeout_none =  {
        }

        rc = RCObjectType(integrations_60)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 60)

        rc = RCObjectType(integrations_60, function_timeout_none)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 60)

        # test only function timeout
        integrations_none =  {
            "integrations": {
            }
        }

        function_timeout_90 =  {
            'timeout': "90"
        }

        rc = RCObjectType(function_opts=function_timeout_90)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 90)

        rc = RCObjectType(integrations_none, function_timeout_90)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 90)

        # test integration and function proxies (override)
        rc = RCObjectType(integrations_60, function_timeout_90)
        timeout = rc.get_timeout()
        self.assertEqual(timeout, 90)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_clientauth(self, RCObjectType):
        rc = RCObjectType()
        cert = rc.get_clientauth()
        self.assertIsNone(cert)


        mock_fn_section = {
            "url": "fake_url.com",
            "client_auth_cert": "cert.pem",
            "client_auth_key": "private.pem"
        }
        rc = RCObjectType(opts=None, function_opts=mock_fn_section)
        cert = rc.get_clientauth()
        self.assertEqual(cert, ("cert.pem", "private.pem"))

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_client_auth(self, RCObjectType):
        rc = RCObjectType()
        cert = rc.get_client_auth()
        self.assertIsNone(cert)


        mock_fn_section = {
            "url": "fake_url.com",
            "client_auth_cert": "cert.pem",
            "client_auth_key": "private.pem"
        }
        rc = RCObjectType(opts=None, function_opts=mock_fn_section)
        cert = rc.get_client_auth()
        self.assertEqual(cert, ("cert.pem", "private.pem"))


        mock_fn_section = {
            "url": "fake_url.com",
            "client_auth_cert": "cert.pem"
        }
        rc = RCObjectType(opts=None, function_opts=mock_fn_section)
        cert = rc.get_client_auth()
        self.assertIsNone(cert)


        mock_fn_section = {
            "url": "fake_url.com",
            "client_auth_cert": mock_paths.MOCK_CLIENT_CERT_FILE,
            "client_auth_key": mock_paths.MOCK_CLIENT_KEY_FILE
        }
        rc = RCObjectType(opts=None, function_opts=mock_fn_section)
        # make sure can still make call to execute with no issues
        resp = self.retry_function(rc.execute, "get", self.URL_TEST_HTTP_VERBS)
        self.assertEqual(resp.status_code, 200)


        rc = RCObjectType()
        # make sure can call execute with clientauth optional parameter
        # but doesn't set the cert value for the whole object
        resp = self.retry_function(rc.execute, "get", self.URL_TEST_HTTP_VERBS, clientauth=(mock_paths.MOCK_CLIENT_CERT_FILE, mock_paths.MOCK_CLIENT_KEY_FILE))
        self.assertEqual(resp.status_code, 200)
        cert = rc.get_client_auth()
        self.assertIsNone(cert)

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    def test_get_no_verify(self, RCObjectType):
        rc = RCObjectType()
        verify = rc.get_verify()
        self.assertIsNone(verify)

    @parameterized.expand([
        [{"verify": "false"}, False, RequestsCommon],
        [{"verify": False}, False, RequestsCommon],
        [{"verify": "true"}, True, RequestsCommon],
        [{"verify": True}, True, RequestsCommon],
        [{"verify": "path_to_CA_bundle"}, "path_to_CA_bundle", RequestsCommon],
        [{"verify": "false"}, False, RequestsCommonWithoutSession],
        [{"verify": False}, False, RequestsCommonWithoutSession],
        [{"verify": "true"}, True, RequestsCommonWithoutSession],
        [{"verify": True}, True, RequestsCommonWithoutSession],
        [{"verify": "path_to_CA_bundle"}, "path_to_CA_bundle", RequestsCommonWithoutSession],
    ])
    def test_get_verify_in_app_section(self, mock_fn_section, expected_verify, RCObjectType):
        rc = RCObjectType(opts=None, function_opts=mock_fn_section)
        verify = rc.get_verify()
        self.assertEqual(verify, expected_verify)

    @parameterized.expand([
        [{"integrations":{"verify": "path_to_CA_bundle"}}, {}, "path_to_CA_bundle", RequestsCommon],
        [{"integrations":{"verify": "true"}}, {}, True, RequestsCommon],
        [{"integrations":{"verify": "false"}}, {}, False, RequestsCommon],
        [{"integrations":{"verify": False}}, {}, False, RequestsCommon],
        [{"integrations":{"verify": "false"}}, {"verify": "path_to_bundle"}, "path_to_bundle", RequestsCommon],
        [{"integrations":{"verify": "path_to_CA_bundle"}}, {}, "path_to_CA_bundle", RequestsCommonWithoutSession],
        [{"integrations":{"verify": "true"}}, {}, True, RequestsCommonWithoutSession],
        [{"integrations":{"verify": "false"}}, {}, False, RequestsCommonWithoutSession],
        [{"integrations":{"verify": False}}, {}, False, RequestsCommonWithoutSession],
        [{"integrations":{"verify": "false"}}, {"verify": "path_to_bundle"}, "path_to_bundle", RequestsCommonWithoutSession]
    ])
    def test_get_verify_in_integrations_section(self, opts, function_opts, expected_verify, RCObjectType):
        rc = RCObjectType(opts=opts, function_opts=function_opts)
        verify = rc.get_verify()
        self.assertEqual(verify, expected_verify)

    @parameterized.expand([
        # mostly here for backward compatibility with older instances of apps using of rc.execute()
        # with a value of `verify` passed in
        # and make sure that the value passed in directly is used over any configs
        ["https://example.com", {}, {"verify": "False"}, True, True, RequestsCommon],
        ["https://example.com", {"integrations": {"verify": True}}, {}, False, False, RequestsCommon],
        ["https://example.com", {}, {}, None, True, RequestsCommon],
        ["https://example.com", {}, {}, "path_to_bundle", "path_to_bundle", RequestsCommon],

        # and make sure that if no value is passed, then the configs are used
        ["https://example.com", {}, {"verify": "False"}, None, False, RequestsCommon],
        ["https://example.com", {"integrations": {"verify": True}}, {}, None, True, RequestsCommon],
        ["https://example.com", {"integrations": {"verify": True}}, {"verify": "False"}, None, False, RequestsCommon],

        # Repeat all tests with RequestsCommonWithoutSession
        ["https://example.com", {}, {"verify": "False"}, True, True, RequestsCommonWithoutSession],
        ["https://example.com", {"integrations": {"verify": True}}, {}, False, False, RequestsCommonWithoutSession],
        ["https://example.com", {}, {}, None, True, RequestsCommonWithoutSession],
        ["https://example.com", {}, {}, "path_to_bundle", "path_to_bundle", RequestsCommonWithoutSession],
        ["https://example.com", {}, {"verify": "False"}, None, False, RequestsCommonWithoutSession],
        ["https://example.com", {"integrations": {"verify": True}}, {}, None, True, RequestsCommonWithoutSession],
        ["https://example.com", {"integrations": {"verify": True}}, {"verify": "False"}, None, False, RequestsCommonWithoutSession]
    ])
    def test_execute_request_with_verify(self, url, opts, function_opts, verify, expected_verify, RCObjectType):
        # this check is to ensure that calling rc.execute() is properly grabbing
        # the value that is given directly to it.
        # The main reason to run this test, is to ensure backward compatibility
        # with apps already using rc.execute() with the `verify` parameter set.
        # in those cases, we want to make sure that we don't override anything with
        # in the app.config, but instead continue to use it as the developer of that
        # app expected it to work


        # register a request mocker to intercept and monitor the requests
        with requests_mock.Mocker() as m:
            m.get(url)
            rc = RCObjectType(opts=opts, function_opts=function_opts)
            self.retry_function(rc.execute, "GET", url, verify=verify)

            # assert that the used value for verify was what we expected
            assert m.request_history[0].verify == expected_verify


    def test_sessions_cookies(self):
        """
        This test proves that the "With Session" version of the RC object
        properly uses the session by retaining cookies from the first request
        NOTE: this is a live test
        """

        # Test with session, where cookies should persist
        rc = RequestsCommon()
        self.retry_function(rc.execute, "GET", "{0}/cookies/set?foo=bar&jon=snow".format(self.URL_TEST_HTTP_VERBS))
        resp = self.retry_function(rc.execute, "GET", "{0}/cookies".format(self.URL_TEST_HTTP_VERBS))

        assert "cookies" in resp.json()
        assert resp.json()["cookies"] == {"foo": "bar", "jon": "snow"}

        # Test again with normal RC object, where cookies won't persist
        rc = RequestsCommonWithoutSession()
        self.retry_function(rc.execute, "GET", "{0}/cookies/set?foo=bar&jon=snow".format(self.URL_TEST_HTTP_VERBS))
        resp = self.retry_function(rc.execute, "GET", "{0}/cookies".format(self.URL_TEST_HTTP_VERBS))

        assert "cookies" in resp.json()
        assert resp.json()["cookies"] == {}

    @unittest.skip(reason="generally true, but not regular enough so closing for now")
    def test_sessions_faster_than_regular(self):
        """
        This test proves that the session object is much more efficient when
        hitting the same endpoint.
        NOTE: this is a live test
        """

        # N needs to be large enough to see a difference (minimum 25 or so)
        # that said, the difference is pretty start even with small iteration numbers
        N = 25

        rc = RequestsCommon()
        start = time.time()
        for i in range(N):
            self.retry_function(rc.execute, "GET", "{0}/basic-auth".format(self.URL_TEST_HTTP_VERBS),
                        headers={"Authorization": "Basic cG9zdG1hbjpwYXNzd29yZA=="})
        end = time.time()
        session_time = end - start

        rc = RequestsCommonWithoutSession()
        start = time.time()
        for i in range(N):
            self.retry_function(rc.execute, "GET", "{0}/basic-auth".format(self.URL_TEST_HTTP_VERBS),
                        headers={"Authorization": "Basic cG9zdG1hbjpwYXNzd29yZA=="})
        end = time.time()
        standard_time = end - start

        assert session_time < standard_time


    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(PY2, reason="retry requires python3.6 or higher")
    def test_retry(self, RCObjectType):
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))
        with pytest.raises(IntegrationError):
            rc.execute("GET", url, retry_tries=3, retry_delay=0.1, retry_backoff=2)

        assert self.caplog.text.count("retrying in") == 2
        assert "retrying in 0.1 seconds..." in self.caplog.text
        assert "retrying in 0.2 seconds..." in self.caplog.text

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(PY2, reason="retry requires python3.6 or higher")
    def test_retry_with_callback_retry_skipped(self, RCObjectType):
        self.caplog.clear()
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))

        # notice that the callback skips the retry logic. this is documented
        # for the callback parameter of rc.execute that when callback doesn't
        # raise an HTTPError, the retry logic is skipped
        rc.execute("GET", url, retry_tries=3, retry_backoff=2, retry_delay=2,
                   callback=lambda x: x)

        assert "retrying in" not in self.caplog.text

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(PY2, reason="retry requires python3.6 or higher")
    def test_retry_with_callback_retry_custom_exception(self, RCObjectType):
        self.caplog.clear()
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))

        def callback_raise_non_default_exception(x):
            raise ValueError(x.status_code)
        # compared to above test, this still raises
        # IntegrationError because of try-except in function
        # but because that isn't in the retry exceptions, it immediately fails.
        # see below how we could make a ValueError raised in a callback trigger a retry
        with pytest.raises(IntegrationError):
            rc.execute("GET", url, retry_tries=3, retry_backoff=2, retry_delay=2,
                    callback=callback_raise_non_default_exception)

        assert "retrying in" not in self.caplog.text

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(PY2, reason="retry requires python3.6 or higher")
    def test_retry_with_callback_retry_custom_exception_expected(self, RCObjectType):
        self.caplog.clear()
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))

        def callback_raise_non_default_exception(x):
            raise ValueError(x.status_code)
        # still raises IntegrationError because of try-except in function
        # but compared to above, the ValueError (inner exception) is listed
        # on the retry list so we see that retries take place
        with pytest.raises(IntegrationError):
            # overwrite the default exception to retry on with ValueError
            # which would be raised in our custom callback
            rc.execute("GET", url, retry_tries=3, retry_exceptions=(ValueError),
                    callback=callback_raise_non_default_exception)

        assert self.caplog.text.count("retrying in") == 2

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(PY2, reason="retry requires python3.6 or higher")
    def test_retry_with_callback_still_retries(self, RCObjectType):
        self.caplog.clear()
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))

        # try again where the retry should kick in because call back DOES raise HTTPError
        with pytest.raises(IntegrationError):
            rc.execute("GET", url, retry_tries=3,
                       callback=lambda x: x.raise_for_status())

        assert self.caplog.text.count("retrying in") == 2

    @parameterized.expand(REQUESTS_COMMON_CLASSES)
    @pytest.mark.skipif(not PY2, reason="make a test for PY2 that ensures retry not engaged")
    def test_retry_PY2_doesnt_retry(self, RCObjectType):
        self.caplog.clear()
        self.caplog.set_level(logging.DEBUG)
        rc = RCObjectType()
        url = "/".join((TestFunctionRequests.URL_TEST_HTTP_VERBS, "status", "401"))

        # should immediately call and fail in PY2
        with pytest.raises(IntegrationError):
            rc.execute("GET", url, retry_tries=3)

        assert "Cannot use retry in resilient_lib.RequestsCommon.execute in Python 2.7" in self.caplog.text
        assert "retrying in" not in self.caplog.text
