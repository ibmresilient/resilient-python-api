import copy
import json
import logging
import unittest
import pytest
from resilient_lib.components.requests_common import RequestsCommon
from resilient_lib.components.integration_errors import IntegrationError

class TestFunctionRequests(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    #rc.execute_call(verb, url, payload, log=None, basicauth=None, verify_flag=True, headers=None,
    #            proxies=None, timeout=None, resp_type=json, callback=None):
    LOG = logging.getLogger(__name__)

    def test_resilient_common_proxies(self):
        integrations = { }

        rc = RequestsCommon(integrations)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { } }
        rc = RequestsCommon(integrations)
        self.assertIsNone(rc.get_proxies())

        integrations = { "integrations": { "https_proxy": "abc" } }
        rc = RequestsCommon(integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertIsNone(proxies['http'])

        integrations = { "integrations": { "https_proxy": "abc", 'http_proxy': 'def' } }
        rc = RequestsCommon(integrations)
        proxies = rc.get_proxies()
        self.assertEqual("abc", proxies['https'])
        self.assertEqual("def", proxies['http'])
        

    def test_resp_types(self):
        IPIFY = "https://api.ipify.org"

        rc = RequestsCommon({})

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
        URL = "https://postman-echo.com"

        headers = {
            "Content-type": "application/json; charset=UTF-8"
        }

        payload = {
            'title': 'foo',
            'body': 'bar',
            'userId': 1
        }

        rc = RequestsCommon({})

        # P O S T
        resp = rc.execute_call("post", "/".join((URL, "post")), payload, headers=headers, log=TestFunctionRequests.LOG)
        self.assertEqual(resp['args'].get("body"), "bar")


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
        URL = "http://httpstat.us" #/200?sleep=5000

        rc = RequestsCommon({})

        resp = rc.execute_call("get", "/".join((URL, "200")), None, resp_type='text')

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", "/".join((URL, "300")), None, resp_type='text')

    def test_statuscode(self):
        URL = "http://httpstat.us/300"

        def callback(resp):
            if resp.status_code != 300:
                raise ValueError(resp.status_code)

        rc = RequestsCommon({})

        resp = rc.execute_call("get", URL, None, resp_type='text', callback=callback)

    def test_timeout(self):
        URL = "http://httpstat.us/200?sleep=30000"

        rc = RequestsCommon({})

        with self.assertRaises(IntegrationError):
            resp = rc.execute_call("get", URL, None, resp_type='text', timeout=10)


    def test_basicauth(self):
        URL = "https://postman-echo.com/basic-auth"
        basicauth = ("postman", "password")

        rc = RequestsCommon({})

        resp = rc.execute_call("get", URL, None, basicauth=basicauth)
        self.assertTrue(resp.get("authenticated"))

    #@pytest.mark.skip(reason="may be over the limit")
    def test_proxy(self):
        rc = RequestsCommon({})

        proxy_url = "https://gimmeproxy.com/api/getProxy"
        proxy_result = rc.execute_call("get", proxy_url, None)

        proxies = {
            'http': proxy_result['curl'] if proxy_result['protocol'] == 'http' else None,
            'https': proxy_result['curl'] if proxy_result['protocol'] == 'https' else None
        }

        URL = "https://api.ipify.org?format=json"

        # J S O N
        json_result = rc.execute_call("get", URL, None, proxies=proxies)

        self.assertTrue(json_result.get("ip"))

        integrations = { "integrations": {
            'http_proxy': proxy_result['curl'] if proxy_result['protocol'] == 'http' else None,
            'https_proxy': proxy_result['curl'] if proxy_result['protocol'] == 'https' else None
          }
        }

        rc = RequestsCommon(integrations)
        json_result = rc.execute_call("get", URL, None)
        self.assertTrue(json_result.get("ip"))

    def test_headers(self):
        # G E T with headers
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "my-sample-header": "my header"
        }
        URL = "https://postman-echo.com/headers"

        rc = RequestsCommon({})

        json_result = rc.execute_call("get", URL, None, headers=headers)
        self.assertEqual(json_result['headers'].get("my-sample-header"), "my header")

