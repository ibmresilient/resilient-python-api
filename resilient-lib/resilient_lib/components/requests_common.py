# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2019. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import requests
import logging
from resilient import is_env_proxies_set, get_and_parse_proxy_env_var, constants as res_constants
from resilient_lib.components.integration_errors import IntegrationError
from resilient_lib.util.lib_common import deprecated


log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class RequestsCommon:
    """
    This class represents common functions around the use of the requests package for REST based APIs.
    It incorporates the app.config section ``[integrations]`` which can be used to define a common set of proxies
    for use by all functions using this library.

    Any similar properties in the function’s section would override the [integrations] properties.

    .. note::
      In the Atomic Function template, as of version 41.1, :class:`RequestsCommon` is instantiated and available available
      in a class that inherits :class:`~resilient_circuits.app_function_component.AppFunctionComponent` as an ``rc`` attribute:

      .. code-block:: python

         response = self.rc.execute(method="get", url=ibm.com)

    :param opts: all configurations found in the app.config file
    :type opts: dict
    :param function_opts: all configurations found in the ``[my_function]`` section of the app.config file
    :type function_opts: dict
    """
    def __init__(self, opts=None, function_opts=None):
        # capture the properties for the integration as well as the global settings for all integrations for proxy urls
        self.integration_options = opts.get('integrations', None) if opts else None
        self.function_opts = function_opts

    def get_proxies(self):
        """
        Proxies can be specified globally for all integrations or specifically per function.

        * If the environmental variables HTTPS_PROXY, HTTP_PROXY and NO_PROXY
          are set, this returns ``None``, as if for a `requests.Request <https://docs.python-requests.org/en/latest/api/#requests.Request>`_.
          If ``proxies`` are ``None``, the environmental variables are used
        * If ``http_proxy`` or ``https_proxy`` is set in the **Function Section** (``[my_function]``) of your app.config file,
          returns a dictionary mapping protocol to the URL of the proxy.
        * If ``http_proxy`` or ``https_proxy`` is set in the **Integrations Section** (``[integrations]``) of your app.config file,
          returns a dictionary mapping protocol to the URL of the proxy.

        :return: A dictionary mapping protocol to the URL of the proxy or ``None``
        :rtype: dict or ``None``
        """
        proxies = None

        if is_env_proxies_set():
            proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTPS_PROXY)

            if not proxy_details:
                proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTP_PROXY)

            if proxy_details:
                log.debug(u"Sending request through proxy: '{0}://{1}:{2}'".format(proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port")))

            return proxies

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

    def execute(self, method, url, timeout=None, proxies=None, callback=None, **kwargs):
        """
        Constructs and sends a request. Returns a
        `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_ object.

        This uses the ``requests.request()`` function to
        make a call. The inputs are mapped to this function.
        See `requests.request() <https://docs.python-requests.org/en/latest/api/#requests.request>`_
        for information on any parameters available, but not documented here.

        :param timeout: Number of seconds to wait for the server to send data
            before sending a float or a timeout tuple (connect timeout, read timeout).
            *See requests docs for more*. If ``None`` it looks in the ``[integrations]``
            section of your app.config for the ``timeout`` setting.
        :type timeout: float or tuple
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
            The mapping protocol must be in the format:

            .. code-block::

                {
                    "https_proxy": "https://localhost:8080,
                    "http_proxy": "http://localhost:8080
                }
        :type proxies: dict
        :param callback: (Optional) Once a response is received from the endpoint,
            return this callback function passing in the ``response`` as its
            only parameter. Can be used to specifically handle errors.
        :type callback: function
        :return: the ``response`` from the endpoint or return ``callback`` if defined.
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_ object
            or ``callback`` function.
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
            log.error(msg)
            raise IntegrationError(msg)

    # Create alias for execute_call_v2
    execute_call_v2 = execute

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
