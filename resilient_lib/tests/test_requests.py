import copy
import json
import logging
import unittest
from resilient_lib.components.requests_common import execute_call
from resilient_lib.components.integration_errors import IntegrationError

class TestFunctionRequests(unittest.TestCase):
    """ Tests for the attachment_hash function"""

    #execute_call(verb, url, payload, log=None, basicauth=None, verify_flag=True, headers=None,
    #            proxies=None, timeout=None, resp_type=json, callback=None):
    LOG = logging.getLogger(__name__)

    def test_resp_types(self):
        IPIFY = "https://api.ipify.org"

        # J S O N
        json_result = execute_call("get", "{}?format=json".format(IPIFY), None)

        try:
            json.dumps(json_result)
        except (TypeError, OverflowError):
            self.fail("result is not json")

        # T E X T
        text_result = execute_call("get", "{}?format=text".format(IPIFY), None, resp_type='text')
        self.assertIsNotNone(text_result)

        # B Y T E S
        bytes_result = execute_call("get", "{}?format=text".format(IPIFY), None, resp_type='bytes')
        self.assertIsNotNone(bytes_result)
        self.assertTrue(isinstance(bytes_result, bytes))


    def test_verbs(self):
        URL = "https://jsonplaceholder.typicode.com/posts"

        headers = {
            "Content-type": "application/json; charset=UTF-8"
        }

        payload = {
            'title': 'foo',
            'body': 'bar',
            'userId': 1
        }

        # P O S T
        resp = execute_call("post", URL, payload, headers=headers, log=TestFunctionRequests.LOG)
        self.assertTrue(resp.get("id"))


        id = 1
        id_url = "/".join((URL, str(id)))
        resp = execute_call("get", id_url, None, log=TestFunctionRequests.LOG)
        self.assertTrue(resp.get("id"))
        self.assertEqual(resp.get("id"), id)


        # P U T
        put_payload = copy.deepcopy(payload)
        put_payload['title'] = 'put'
        put_payload['id'] = id

        resp = execute_call("put", id_url, put_payload, headers=headers, log=TestFunctionRequests.LOG)
        TestFunctionRequests.LOG.info(resp)
        self.assertTrue(resp.get("title"))
        self.assertEqual(resp.get("title"), 'put')

        # P A T C H
        patch = {
            'title': 'patch'
        }

        resp = execute_call("patch", id_url, patch, headers=headers, log=TestFunctionRequests.LOG)
        self.assertTrue(resp.get("title"))
        self.assertEqual(resp.get("title"), 'patch')

        # D E L E T E
        resp = execute_call("delete", id_url, None, log=TestFunctionRequests.LOG)

        # bad verb
        with self.assertRaises(IntegrationError):
            resp = execute_call("bad", id_url, None, log=TestFunctionRequests.LOG)

    def test_statuscode(self):
        URL = "http://httpstat.us" #/200?sleep=5000

        resp = execute_call("get", "/".join((URL, "200")), None, resp_type='text')

        with self.assertRaises(IntegrationError):
            resp = execute_call("get", "/".join((URL, "300")), None, resp_type='text')

    def test_statuscode(self):
        URL = "http://httpstat.us/300"

        def callback(resp):
            if resp.status_code != 300:
                raise ValueError(resp.status_code)

        resp = execute_call("get", URL, None, resp_type='text', callback=callback)

    def test_timeout(self):
        URL = "http://httpstat.us/200?sleep=30000"

        with self.assertRaises(IntegrationError):
            resp = execute_call("get", URL, None, resp_type='text', timeout=10)


    def test_basicauth(self):
        URL = "https://postman-echo.com/basic-auth"
        basicauth = ("postman", "password")

        resp = execute_call("get", URL, None, basicauth=basicauth)
        self.assertTrue(resp.get("authenticated"))

    def test_proxy(self):
        proxy_url = "https://gimmeproxy.com/api/getProxy"

        proxy_result = execute_call("get", proxy_url, None)

        proxies = {
            'http': proxy_result['curl'] if proxy_result['protocol'] == 'http' else None,
            'https': proxy_result['curl'] if proxy_result['protocol'] == 'https' else None
        }

        URL = "https://api.ipify.org?format=json"

        # J S O N
        json_result = execute_call("get", URL, None, proxies=proxies)

        self.assertTrue(json_result.get("ip"))

    def test_headers(self):
        # G E T with headers
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "my-sample-header": "my header"
        }
        URL = "https://postman-echo.com/headers"

        json_result = execute_call("get", URL, None, headers=headers)
        self.assertEqual(json_result['headers'].get("my-sample-header"), "my header")

