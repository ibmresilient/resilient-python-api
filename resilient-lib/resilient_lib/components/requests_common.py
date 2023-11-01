# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2023. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

import logging

import requests
from deprecated import deprecated
from resilient_lib.components.integration_errors import IntegrationError
from resilient_lib.components.resilient_common import str_to_bool
from retry.api import retry_call
from six import PY2

from resilient import constants as res_constants
from resilient import get_and_parse_proxy_env_var, is_env_proxies_set

LOG = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class RequestsCommon(object):
    """
    This class represents common functions around the use of the requests package for REST based APIs.
    It incorporates the app.config section ``[integrations]`` which can be used to define a common set of proxies
    for use by all functions using this library.

    Any similar properties in the function’s section would override the [integrations] properties.

    .. note::
      In the Atomic Function template, as of version 41.1, :class:`RequestsCommon` is instantiated and available
      in a class that inherits :class:`~resilient_circuits.app_function_component.AppFunctionComponent` as an ``rc`` attribute:

      .. code-block:: python

         response = self.rc.execute(method="GET", url="ibm.com")

    :param opts: all configurations found in the app.config file
    :type opts: dict
    :param function_opts: all configurations found in the ``[my_function]`` section of the app.config file
    :type function_opts: dict
    """
    def __init__(self, opts=None, function_opts=None):
        # capture the properties for the integration as well as the global settings for all integrations for proxy urls
        self.integration_options = opts.get("integrations", None) if opts else None
        self.function_opts = function_opts

        # base class requests object (i.e. with persistent sessions):
        self.request_obj = requests.Session()

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
                LOG.debug(u"Sending request through proxy: '%s://%s:%s'", proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port"))

            return proxies

        if self.integration_options and (self.integration_options.get("http_proxy") or self.integration_options.get("https_proxy")):
            proxies = {'http': self.integration_options.get("http_proxy"), 'https': self.integration_options.get("https_proxy")}

        if self.function_opts and (self.function_opts.get("http_proxy") or self.function_opts.get("https_proxy")):
            proxies = {'http': self.function_opts.get("http_proxy"), 'https': self.function_opts.get("https_proxy")}

        return proxies

    def get_timeout(self):
        """
        Get the default timeout value in the **Function Section** (``[my_function]``) of your app.config file,
        or from the **Integrations Section** (``[integrations]``) of your app.config file.

        ``[my_function]`` section takes precedence over ``[integrations]`` section value.

        :return: timeout value
        :rtype: int
        """
        timeout = DEFAULT_TIMEOUT

        if self.integration_options and self.integration_options.get("timeout"):
            timeout = self.integration_options.get("timeout")

        if self.function_opts and self.function_opts.get("timeout"):
            timeout = self.function_opts.get("timeout")

        return int(timeout)

    def get_client_auth(self):
        """
        A client certificate for authenticating calls to external endpoints can be specified on a per function basis.

        If ``client_auth_cert`` and ``client_auth_key`` are set in the **Function Section** (``[my_function]``) of your app.config file,
        returns a tuple containing the respective paths to the certificate and private key for the client cert.

        Example:

          .. code-block::

            [my_function]
            ...
            client_auth_cert = <path_to_cert.pem>
            client_auth_key = <path_to_cert_private_key.pem>

        :return: The filepaths for the client side certificate and the private key as a tuple of both files' paths
                 or ``None`` if either one of the values are missing
        :rtype: tuple(str, str)
        """
        cert = None

        if self.function_opts and (self.function_opts.get("client_auth_cert") and self.function_opts.get("client_auth_key")):
            cert = (self.function_opts.get("client_auth_cert"), self.function_opts.get("client_auth_key"))

        return cert

    def get_verify(self):
        """
        Get ``verify`` parameter from app config or from env var
        ``REQUESTS_CA_BUNDLE`` which is the default way to set
        verify with python requests library.

        Value can be set in ``[integrations]`` or in the ``[fn_my_app]`` section

        Value in ``[fn_my_app]`` takes precedence over ``[integrations]``
        which takes precedence over ``REQUESTS_CA_BUNDLE``

        :param app_options: App config dict
        :type app_options: dict
        :return: Value to set ``requests.session.verify`` to.
            Either a path or a boolean
        :rtype: bool or str or None (which will default to requests default which is ``True``)
        """
        verify = None

        # look in app's config section first
        if self.function_opts:
            verify = self.function_opts.get("verify", True)

        # if not found in config, then [integration] wide section can be used;
        # NOTE: this is pretty much limited to just integration server envs
        # as most app host deployments will just be the single app, and thus
        # an integration's wide setting section is not relevant
        if verify is None and self.integration_options:
            verify = self.integration_options.get("verify", True)

        # convert potential strings to boolean if necessary
        # NOTE: it is possible that a string path should be returned,
        # in which case we don't want there to be a boolean conversion
        if isinstance(verify, str) and verify.lower() in ["false", "true"]:
            verify = str_to_bool(verify)

        return verify

    # alias for existing instances of ``get_clientauth``, but from now on
    # should use ``get_client_auth``
    get_clientauth = get_client_auth


    def execute(self, method, url, timeout=None, proxies=None, callback=None, clientauth=None, verify=None,
                retry_tries=1, retry_delay=1, retry_max_delay=None, retry_backoff=1, retry_jitter=0,
                retry_exceptions=requests.exceptions.HTTPError, **kwargs):
        """
        Constructs and sends a request. Returns a
        `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_ object.

        This uses the ``requests.request()`` function to
        make a call. The inputs are mapped to this function.
        See `requests.request() <https://docs.python-requests.org/en/latest/api/#requests.request>`_
        for information on any parameters available, but not documented here.

        Retries can be achieved through the parameters prefixed with ``retry_<param>``. Retry is only available in PY3+.

        :param method: Rest method to execute (``GET``, ``POST``, etc...)
        :type method: str
        :param url: URL to execute request against
        :type url: str
        :param timeout: (Optional) Number of seconds to wait for the server to send data
            before sending a float or a timeout tuple (connect timeout, read timeout).
            *See requests docs for more*. If ``None`` it looks in the ``[integrations]``
            section of your app.config for the ``timeout`` setting.
        :type timeout: float or tuple
        :param proxies: (Optional) Dictionary mapping protocol to the URL of the proxy.
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
            If ``callback`` is given, any retry parameters will be ignored
            unless the ``callback`` function raises an error in the parameter
            ``retry_exceptions`` (see below) in which case the retry logic will kick in.

            **Example:**

            .. code-block:: python

                from resilient_lib import IntegrationError, RequestsCommon

                def custom_callback(response):
                    \"\"\" custom callback function to handle 400 error codes \"\"\"
                    if response.status_code >= 400 and response.status_code < 500:
                        # raise ValueError which will be retried
                        raise ValueError("retry me")
                    else:
                        # all other status codes should return normally
                        # note this bypasses the normal rc.execute logic which
                        # would raise an error other 500 errors
                        return response

                rc = RequestsCommon()
                try:
                    # will retry 3 times then will raise IntegrationError
                    response = rc.execute("GET", "https://postman-echo.com/status/404", 
                                               callback=custom_callback, retry_tries=3,
                                               retry_exceptions=ValueError)
                except IntegrationError as err:
                    print(err)

        :type callback: function
        :param clientauth: (Optional) Equivalent to the ``cert`` parameter of ``requests``.
            Client-side certificates can be configured automatically in
            the app's section of the app.config. These values will be read in automatically by
            ``RequestsCommon`` when ``execute`` is called.

            Example:

            .. code-block::

                [resilient]
                ... # configs for connection to SOAR

                [fn_my_app]
                ... # some other configs
                client_auth_cert=<path_to_client_auth_cert_file>
                client_auth_key=<path_to_client_auth_private_key_file>

            If not set in the app.config file, the filepath for the client side certificate and the
            private key can be passed to this function either as the path to a single file or as a
            tuple of both files' paths.
        :type clientauth: str or tuple(str, str)
        :param verify: (Optional) Either a boolean, in which case it controls whether requests verifies
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``None`` as passed in here. If ``None``,
            then the value is searched for in the app's section of the app.config. If no value
            is found, then the requests.request() default of ``True`` is used. In that case,
            the CA bundle found at ``requests.utils.DEFAULT_CA_BUNDLE_PATH`` is the CA bundle used,
            which is usually a bundle provided by Mozilla. Setting ``verify=True`` is the safest option
            and should only be changed if you have a self-signed certificate or you want to bypass
            SSL for testing purposes. A production level app should never disable SSL verification
            completely.

            Example:

            .. code-block::

                [fn_my_app]
                ... # some other configs
                verify=<path/to/CA/bundle/to/use>

            .. note::
                The value held in the app's config will be overwritten if a value is passed in by the call to ``execute``.
        :type verify: bool or str
        :param retry_tries: (PY3 only) The maximum number of attempts. Default: ``1`` (no retry). Use ``-1`` for unlimited retries.
            Matches ``tries`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_tries: int
        :param retry_delay: (PY3 only) Initial delay between attempts. Default: ``1``.
            Matches ``delay`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_delay: int
        :param retry_max_delay: (PY3 only) The maximum value of delay. Default: ``None`` (no limit).
            Matches ``max_delay`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_max_delay: int
        :param retry_backoff: (PY3 only) Multiplier applied to delay between attempts. Default: ``1`` (no backoff).
            Matches ``backoff`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_backoff: int
        :param retry_jitter: (PY3 only) Extra seconds added to delay between attempts. Default: ``0``.
            Fixed if a number, random if a range tuple (min, max).
            Matches ``jitter`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_jitter: int | tuple(int, int)
        :param retry_exceptions: (PY3 only) An exception or a tuple of exceptions to catch.
            Default: ``requests.exceptions.HTTPError``.
            Matches ``exceptions`` parameter of `retry.api.retry_call <https://github.com/eSAMTrade/retry#retry_call>`_.
        :type retry_exceptions: Exception | tuple(Exception)
        :return: the ``response`` from the endpoint or return ``callback`` if defined.
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_ object
            or ``callback`` function.
        """
        try:
            if method.lower() not in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
                raise IntegrationError("unknown method {}".format(method))

            # If proxies was not set check if they are set in the config
            if not proxies:
                proxies = self.get_proxies()

            if not timeout:
                timeout = self.get_timeout()

            if not clientauth:
                clientauth = self.get_client_auth()

            if verify is None:
                verify = self.get_verify()

            # Log the parameter inputs that are not None
            args_dict = locals()
            # When debugging execute_call_v2 in PyCharm you may get an exception when executing the for-loop:
            # Dictionary changed size during iteration.
            # To work around this while debugging you can change the following line to:
            # args = list(args_dict.keys())
            args = args_dict.keys()
            for k in args:
                if k != "self" and k != "kwargs" and args_dict[k] is not None:
                    LOG.debug("  %s: %s", k, args_dict[k])

            # define inner func to allow for retry
            # by doing it this way, we don't have to mess with
            # retry's strange way of passing arguments -- we just
            # can call it directly because the args are available
            # from the outer function
            def __execute_request_retriable():
                # Pass request to requests.request() function
                response = self.request_obj.request(method, url, timeout=timeout, proxies=proxies, cert=clientauth, verify=verify, **kwargs)

                # Debug logging
                LOG.debug(response.status_code)
                LOG.debug(response.content)

                # custom handler for response handling
                # set callback to be the name of the method you would like to call
                # to do your custom error handling and return the response
                # NOTE: this will potentially bypass any retry if
                # the error raised in callback is not matched to the
                # ``retry_exceptions`` parameter. By default, that means
                # that if HTTPError is not raised in callback, retry
                # will not behave as expected
                if callback:
                    return callback(response)

                # Raise error is bad status code is returned
                response.raise_for_status()

                # Return requests.Response object
                return response
            
            # NOTE: because retry library requires PY3 style exceptions,
            # if version running on is PY2, retries won't be allowed
            if PY2 and retry_tries != 1:
                LOG.warning("Cannot use retry in resilient_lib.RequestsCommon.execute in Python 2.7. Please upgrade your app to run on Python 3.9 or greater")
                retry_tries = 1

            # make call with retry wrapper. if tries is set to 1,
            # will just execute normally. otherwise will engage retry
            # logic as applicable
            return retry_call(
                __execute_request_retriable,
                exceptions=retry_exceptions,
                tries=retry_tries,
                delay=retry_delay,
                backoff=retry_backoff,
                max_delay=retry_max_delay,
                jitter=retry_jitter,
                logger=LOG
            )

        except Exception as err:
            msg = str(err)
            LOG.error(msg)
            raise IntegrationError(msg)

    # Create alias for execute_call_v2
    execute_call_v2 = execute

    @deprecated(version="v34.0", reason="Use the new method execute()")
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

            if not resp:
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

class RequestsCommonWithoutSession(RequestsCommon):
    """
    This class extends :class:`RequestsCommon` maintaining the behavior of 
    ``RequestsCommon`` that was present in versions <= 47.1.x.

    The difference is that every time :class:`RequestsCommonWithoutSession.execute()`
    is called, this class will use ``requests.request`` to execute the request, while
    :class:`RequestsCommon.execute()` uses ``Session().request``.

    This class is interchangeable with :class:`RequestsCommon` and code that uses
    :class:`RequestsCommon` can be simiply refactored to use :class:`RequestsCommonWithoutSession`

    :param args: positional arguments matching :class:`RequestsCommon`
    :type args: list
    :param kwargs: named keyword arguments matching :class:`RequestsCommon`
    :type kwargs: dict
    """
    def __init__(self, *args, **kwargs):
        super(RequestsCommonWithoutSession, self).__init__(*args, **kwargs)
        self.request_obj = requests


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
