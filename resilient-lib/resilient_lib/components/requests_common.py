# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2019. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import requests
import logging
from resilient_lib.components.integration_errors import IntegrationError
from resilient_lib.util.lib_common import deprecated


log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class RequestsCommon:
    """
    This class represents common functions around the use of the requests package for REST based APIs.
    It incorporates the app.config section "integrations" which can be used to define a common set of proxies
    for use by all functions using this library:

    [integrations]
    http_proxy=
    https_proxy=

    Similar properties may exist in the function's section which would override the [integrations] properties.
    """
    def __init__(self, opts=None, function_opts=None):
        # capture the properties for the integration as well as the global settings for all integrations for proxy urls
        self.integration_options = opts.get('integrations', None) if opts else None
        self.function_opts = function_opts

    def get_proxies(self):
        """ proxies can be specified globally for all integrations or specifically per function """
        proxies = None
        if self.integration_options and (self.integration_options.get("http_proxy") or self.integration_options.get("https_proxy")):
            proxies = {'http': self.integration_options.get("http_proxy"), 'https': self.integration_options.get("https_proxy")}

        if self.function_opts and (self.function_opts.get("http_proxy") or self.function_opts.get("https_proxy")):
            proxies = {'http': self.function_opts.get("http_proxy"), 'https': self.function_opts.get("https_proxy")}

        return proxies

    def get_timeout(self):
        """
        get the default timeout value in the 'integrations' section or the function's own section
        :return: timeout value
        """
        timeout = DEFAULT_TIMEOUT

        if self.integration_options and self.integration_options.get("timeout"):
            timeout = self.integration_options.get("timeout")

        if self.function_opts and self.function_opts.get("timeout"):
            timeout = self.function_opts.get("timeout")

        return int(timeout)

    def execute_call_v2(self, method, url, timeout=None, proxies=None, callback=None, **kwargs):
        """Constructs and sends a request. Returns :class:`Response` object.

            From the requests.requests() function, inputs are mapped to this function
            :param method: GET, HEAD, PATCH, POST, PUT, DELETE, OPTIONS
            :param url: URL for the request.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the body of the :class:`Request`.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
            :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
            :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            :param timeout: (optional) How many seconds to wait for the server to send data
                before giving up, as a float, or a :ref:`(connect timeout, read
                timeout) <timeouts>` tuple.
            :type timeout: float or tuple
            :param allow_redirects: (optional) Boolean. Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``True``.
            :type allow_redirects: bool
            :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
            :param verify: (optional) Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
            :param stream: (optional) if ``False``, the response content will be immediately downloaded.
            :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
            :param callback: callback routine used to handle errors
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        try:
            if method.lower() not in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
                raise IntegrationError("unknown method {}".format(method))

            # If proxies was not set check if they are set in the config
            if proxies is None:
                proxies = self.get_proxies()

            if timeout is None:
                timeout = self.get_timeout()

            # Log the parameter inputs that are not None
            args_dict = locals()
            # When debugging execute_call_v2 in PyCharm you may get an exception when executing the for-loop:
            # Dictionary changed size during iteration.
            # To work around this while debugging you can change the following line to:
            # args = list(args_dict.keys())
            args = args_dict.keys()
            for k in args:
                if k != "self" and k != "kwargs" and args_dict[k] is not None:
                    log.debug("  {}: {}".format(k, args_dict[k]))

            # Pass request to requests.request() function
            response = requests.request(method, url, timeout=timeout, proxies=proxies, **kwargs)

            # Debug logging
            log.debug(response.status_code)
            log.debug(response.content)

            # custom handler for response handling
            # set callback to be the name of the method you would like to call
            # to do your custom error handling and return the response
            if callback:
                return callback(response)

            # Raise error is bad status code is returned
            response.raise_for_status()

            # Return requests.Response object
            return response

        except Exception as err:
            msg = str(err)
            log and log.error(msg)
            raise IntegrationError(msg)

    @deprecated("Use the new method execute_call_v2()")
    def execute_call(self, verb, url, payload={}, log=None, basicauth=None, verify_flag=True, headers=None,
                     proxies=None, timeout=None, resp_type='json', callback=None):
        """
        Function: perform the http API call. Different types of http operations are supported:
        GET, HEAD, PATCH, POST, PUT, DELETE
        Errors raise IntegrationError
        If a callback method is provided, then it's called to handle the error

        When using argument 'json' Content-Type will automatically be set to "application/json" by requests lib.

        :param verb: GET, HEAD, PATCH, POST, PUT, DELETE
        :param url:
        :param basicauth: used for basic authentication - (user, password)
        :param payload:
        :param log: optional log statement
        :param verify_flag: True/False - False used for debugging generally
        :param headers: dictionary of http headers
        :param proxies: http and https proxies for call
        :param timeout: timeout before call should abort
        :param resp_type: type of output to return: json, text, bytes
        :param callback: callback routine used to handle errors
        :return: json of returned data
        """

        try:
            (payload and log) and log.debug(payload)

            if verb.lower() not in ('get', 'post', 'put', 'patch', 'delete', 'head'):
                raise IntegrationError("unknown verb {}".format(verb))

            if proxies is None:
                proxies = self.get_proxies()

            if verb.lower() == 'post':

                content_type = get_case_insensitive_key_value(headers, "Content-Type")

                if is_payload_in_json(content_type):
                    resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, json=payload,
                                            auth=basicauth, timeout=timeout, proxies=proxies)
                else:
                    resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, data=payload,
                                            auth=basicauth, timeout=timeout, proxies=proxies)
            else:
                resp = requests.request(verb.upper(), url, verify=verify_flag, headers=headers, params=payload,
                                        auth=basicauth, timeout=timeout, proxies=proxies)

            if resp is None:
                raise IntegrationError('no response returned')

            # custom handler for response handling?
            if callback:
                return callback(resp)

            # standard error handling
            if resp.status_code >= 300:
                # get the result
                # log resp.status_code in case resp.text isn't available
                raise IntegrationError(
                    "status_code: {}, msg: {}".format(resp.status_code, resp.text if resp.text else "N/A"))

            # check if anything returned
            log and log.debug(resp.text)

            # get the result
            if resp_type == 'json':
                r = resp.json()
            elif resp_type == 'text':
                r = resp.text
            elif resp_type == 'bytes':
                r = resp.content
            else:
                raise IntegrationError("incorrect response type: {}".format(resp_type))

            # Produce a IntegrationError with the return value
            return r      # json object needed, not a string representation
        except Exception as err:
            msg = str(err)
            log and log.error(msg)
            raise IntegrationError(msg)


def is_payload_in_json(content_type):
    """
    Verify the content_type.
    If "Content-Type" is NOT specified pass the payload to the "json" argument - return True.

    If "Content-Type" is specified:
        - if the value is "application/json" pass the payload to the "json" argument - return True.
        - if the value is NOT "application/json" pass the payload to the "data" argument - return False.
    :param content_type:
    :return: True or False
    """

    if not content_type:
        return True

    return "application/json" in content_type.lower()


def get_case_insensitive_key_value(dictionary, key):
    """
    Get case insensitive key value from dictionary.
    :param dictionary:
    :param key:
    :return: value or None
    """
    if dictionary is None:
        return None

    return next((v for k, v in dictionary.items() if k.lower() == key.lower()), None)
