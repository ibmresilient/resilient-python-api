# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Base client for Resilient REST API"""
from __future__ import print_function

import json
import logging
import mimetypes
import os
import ssl
import sys
import traceback
import unicodedata

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from requests.packages.urllib3.poolmanager import PoolManager
from requests_toolbelt.multipart.encoder import MultipartEncoder
from retry.api import retry_call

from resilient import constants, helpers

try:
    # Python 3
    import urllib.parse as urlparse
except:
    # Python 2
    import urlparse

LOG = logging.getLogger(__name__)


class TLSHttpAdapter(HTTPAdapter):
    """
    Adapter that ensures that we use the best available SSL/TLS version.
    Some environments default to SSLv3, so we need to specifically ask for
    the highest protocol version that both the client and server support.
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLS if sys.version_info.major == 2 else ssl.PROTOCOL_TLS_CLIENT)


class BasicHTTPException(Exception):
    """Base exception for HTTP errors."""
    def __init__(self, response, err_reason=u"Unknown Reason", err_text=u"Unknown Error"):
        """
        Args:
          response - the Response object from the get/put/etc.
        """
        err_reason = response.reason if response.reason else err_reason
        err_text = response.text if response.text else err_text

        err_message = u"'resilient' API Request FAILED:\nResponse Code: {0}\nReason: {1}. {2}".format(response.status_code, err_reason, err_text)

        # Add a __qualname__ attribute if does not exist - needed for PY27
        if not hasattr(BasicHTTPException, "__qualname__"):
            setattr(BasicHTTPException, "__qualname__", BasicHTTPException.__name__)

        super(BasicHTTPException, self).__init__(err_message)

        self.response = response

    def get_response(self):
        return self.response


class RetryHTTPException(BasicHTTPException):
    """Exception for HTTP errors that should be retried."""
    def __init__(self, response, err_reason=u"Unknown Reason", err_text=u"Unknown Error"):
        """
        Args:
          response - the Response object from the get/put/etc.
        """
        super(RetryHTTPException, self).__init__(response, err_reason=err_reason, err_text=err_text)

    @staticmethod
    def raise_if_error(response, skip_retry=[]):
        """
        Raise a RetryError if a non-401 status is returned
        AND the status is not in the set of statuses to skip retry on.

        NOTE: 401 errors are unrecoverable as they indicated an unauthorized
        connection. These errors result in circuits stopping itself. This is
        achieved by capturing the stack trace and sending a sys.exit().

        :param response: requests.Response object
        :type response: requests.Response
        :param skip_retry: list of status codes to not retry, defaults to []
        :type skip_retry: list[int], optional
        :raises RetryHTTPException: if error status and should be retried
        :raises BasicHTTPException: if error but should not be retried
        """

        if response.status_code == 401:
            try:
                raise RetryHTTPException(response, err_reason=constants.ERROR_MSG_CONNECTION_UNAUTHORIZED, err_text=constants.ERROR_MSG_CONNECTION_INVALID_CREDS)
            except RetryHTTPException:
                traceback.print_exc()
                sys.exit(constants.ERROR_CODE_CONNECTION_UNAUTHORIZED)

        elif response.status_code >= 300:
            # these exceptions should not be retried
            if response.status_code not in fix_list(skip_retry):
                raise RetryHTTPException(response)
            else:
                raise BasicHTTPException(response)

def fix_list(value):
    """fix values to always use lists

    :param value: value to test if not a list
    :type value: list, int
    :return: converted value if not a list
    :rtype: list
    """
    if value == None:
        return []
    return value if isinstance(value, list) else [value]

class NoChange(Exception):
    """
    Exception that can be raised within a get/put handler or a patch callback
    to indicate 'no change' (which then just bypasses the update operation).
    """
    pass


def ensure_unicode(input_value):
    """ if input_value is type str, convert to unicode with utf-8 encoding """
    if sys.version_info.major >= 3:
        return input_value

    if not isinstance(input_value, basestring):
        return input_value
    if isinstance(input_value, str):
        input_unicode = input_value.decode('utf-8')
    else:
        input_unicode = input_value

    input_unicode = unicodedata.normalize('NFKC', input_unicode)
    return input_unicode


def get_proxy_dict(opts):
    """ Creates a dictionary with proxy config to be sent to the SimpleClient """
    scheme = urlparse.urlparse(opts['proxy_host']).scheme
    if not scheme:
        scheme = 'https'
        proxy_host = opts['proxy_host']
    else:
        proxy_host = opts['proxy_host'][len(scheme + "://"):]

    if opts.get('proxy_user') and opts.get('proxy_password'):
        proxy = {'https': '{0}://{1}:{2}@{3}:{4}/'.format(scheme, opts['proxy_user'], opts['proxy_password'],
                                                          proxy_host, opts['proxy_port'])}
    else:
        proxy = {'https': '{0}://{1}:{2}'.format(scheme, proxy_host, opts['proxy_port'])}

    return proxy


class BaseClient(object):
    """Helper for using SOAR REST API."""

    def __init__(self, org_name=None, base_url=None, proxies=None, verify=None, certauth=None, custom_headers=None, **kwargs):
        """
        :param org_name: The name of the organization to use
        :type org_name: str
        :param base_url: The base URL of the SOAR server, e.g. ``https://soar.ibm.com/``
        :type base_url: str
        :param proxies: A dictionary of ``HTTP`` proxies to use, if any
        :type proxies: dict
        :param verify: The path to a ``PEM`` file containing the trusted CAs, or ``False`` to disable all TLS verification
        :type verify: str|bool
        :param certauth: The filepath for the client side certificate and the private key either as a single file or as a tuple of both files' paths
        :type certauth: str|tuple(str, str)
        :param custom_headers: A dictionary of any headers you want to send in **every** request
        :type custom_headers: dict
        :param kwargs: A dictionary of any other keyword arguments
        :type kwargs: dict
        """

        base_headers = {
            "content-type": "application/json",
            constants.HEADER_MODULE_VER_KEY: constants.HEADER_MODULE_VER_VALUE
        }

        if custom_headers and isinstance(custom_headers, dict):
            base_headers.update(custom_headers)

        self.headers = base_headers

        self.cookies = None
        self.org_id = None
        self.user_id = None
        self.base_url = u'https://app.resilientsystems.com/'
        self.org_name = ensure_unicode(org_name)
        if proxies:
            self.proxies = {ensure_unicode(key): ensure_unicode(proxies[key]) for key in proxies}
        else:
            self.proxies = None
        if helpers.is_env_proxies_set():
            self.proxies = None
        if base_url:
            self.base_url = ensure_unicode(base_url)
        self.verify = verify
        self.verify = ensure_unicode(verify)
        if verify is None:
            self.verify = True
        self.authdata = None
        self.session = requests.Session()
        self.session.mount(u'https://', TLSHttpAdapter())

        # API key
        self.api_key_id = None
        self.api_key_secret = None
        self.use_api_key = False
        self.api_key_handle = None      # This is the principle ID for an api key. Also called handle

        # Client Cert based authentication
        self.cert = certauth

        # Retry configs
        self.max_connection_retries = kwargs.get(constants.APP_CONFIG_MAX_CONNECTION_RETRIES) if kwargs.get(constants.APP_CONFIG_MAX_CONNECTION_RETRIES) is not None else constants.APP_CONFIG_MAX_CONNECTION_RETRIES_DEFAULT
        self.request_max_retries = kwargs.get(constants.APP_CONFIG_REQUEST_MAX_RETRIES) if kwargs.get(constants.APP_CONFIG_REQUEST_MAX_RETRIES) is not None else constants.APP_CONFIG_REQUEST_MAX_RETRIES_DEFAULT
        self.request_retry_delay = kwargs.get(constants.APP_CONFIG_REQUEST_RETRY_DELAY) if kwargs.get(constants.APP_CONFIG_REQUEST_RETRY_DELAY) is not None else constants.APP_CONFIG_REQUEST_RETRY_DELAY_DEFAULT
        self.request_retry_backoff = kwargs.get(constants.APP_CONFIG_REQUEST_RETRY_BACKOFF) if kwargs.get(constants.APP_CONFIG_REQUEST_RETRY_BACKOFF) is not None else constants.APP_CONFIG_REQUEST_RETRY_BACKOFF_DEFAULT

    def set_api_key(self, api_key_id, api_key_secret, timeout=None, include_permissions=False):
        """
        Call this method instead of the connect method in order to use API key
        Just like the connect method, this method calls the session endpoint
        to get org_id information.
        :param api_key_id: api key ID to use to connect
        :type api_key_id: string
        :param api_key_secret: associated secret
        :type api_key_secret: string
        :param timeout: timeout limit if desired. None by default
        :type timeout: float
        :param include_permissions: whether to include permissions in call to /rest/session.
            Since SOAR v48 this param has been included and set to "true" by default on the server
            (until v50 where it will be removed). We don't need permission details in circuits so we
            set it to False by default, but if there is a use of this elsewhere in app code,
            and either "perms" or "effective_permissions" details that are returned by the
            endpoint are needed, the value here should be set to True.
        :type include_permissions: bool
        :return:
        """
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.use_api_key = True

        if include_permissions:
            LOG.debug("'include_permissions' is deprecated and scheduled to be removed in v50, use GET " +
                        "/rest/session/{org_id}/acl instead.\n\t\tAt that time, 'include_permissions' will be " +
                        "removed and this endpoint will not return org permissions.")

        # Wrap self.session.get and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __set_api_key():
            r = self.session.get(u"{0}/rest/session?include_permissions={1}".format(self.base_url, "true" if include_permissions else "false"),
                                 auth=HTTPBasicAuth(self.api_key_id, self.api_key_secret),
                                 proxies=self.proxies,
                                 headers=self.make_headers(),
                                 verify=self.verify,
                                 timeout=timeout,
                                 cert=self.cert)
            RetryHTTPException.raise_if_error(r)
            return r

        response = retry_call(__set_api_key,
                              exceptions=(RetryHTTPException, ConnectionError),
                              tries=self.max_connection_retries,
                              delay=self.request_retry_delay,
                              backoff=self.request_retry_backoff)

        session = json.loads(response.text)
        self._extract_org_id(session)
        self.api_key_handle = session.get("api_key_handle", None)
        return session

    def connect(self, email, password, timeout=None):
        """Performs connection, which includes authentication.

        Args:
          email - the email address to use for authentication.
          password - the password
          timeout - number of seconds to wait for response
        Returns:
          The Resilient session object (dict)
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """
        LOG.warning(constants.WARNING_DEPRECATE_EMAIL_PASS)
        self.authdata = {
            u'email': ensure_unicode(email),
            u'password': ensure_unicode(password)
        }
        return self._connect(timeout=timeout)

    def _extract_org_id(self, response):
        """
        Extract the org's id from server response. Loops the orgs
        in the response and checks each ``cloud_account``, ``uuid``
        or ``name`` against the ``org_name`` attribute in the 
        app.config file to see if it matches any of the 3.

        If found, sets ``self.org_id`` equal to the ``id`` of the org

        Also sets ``self.all_orgs`` equal to the full list of orgs
        that are ``enabled`` for that user

        :param response: server response from session endpoint
        :type response: dict
        :raises Exception: if user is not a member of any orgs
        :raises Exception: if ``org_name`` value in app.config is not set
        :raises Exception: if the user is not a member of the org specified in the app.config
        :raises Exception: if the org specified has an ``enabled`` state set to ``False``
        """
        app_config_org_value = self.org_name
        selected_org = None
        orgs = response.get("orgs", [])

        if not orgs:
            raise Exception("User is not a member of any orgs")

        if not app_config_org_value:
            org_names = [org.get("name") for org in orgs]
            msg = u"Please specify the organization name to which you want to connect.\n" + \
                  u"The user is a member of the following organizations: '{0}'"
            raise Exception(msg.format(u"', '".join(org_names)))

        for o in orgs:

            if app_config_org_value == o.get("cloud_account", ""):
                LOG.info("Using cloud account id: %s", app_config_org_value)
                selected_org = o
                break

            if app_config_org_value == o.get("uuid", ""):
                LOG.info("Using org uuid: %s", app_config_org_value)
                selected_org = o
                break

            if ensure_unicode(app_config_org_value) == o.get("name", ""):
                LOG.info("Using org name: %s", app_config_org_value)
                selected_org = o
                break

        if not selected_org:
            msg = u"The user is not a member of the specified organization '{0}'."
            raise Exception(msg.format(self.org_name))

        if not selected_org.get("enabled", False):
            msg = "This organization is not accessible to you.\n\n" \
                  "This can occur because of one of the following:\n\n" \
                  "The organization does not allow access from your current IP address.\n" \
                  "The organization requires authentication with a different provider than you are currently using.\n" \
                  "Your IP address is {0}"
            raise Exception(msg.format(response.get("session_ip", "Unknown")))

        self.all_orgs = [org for org in orgs if org.get("enabled")]
        self.org_id = selected_org.get("id", None)

    def _connect(self, timeout=None, include_permissions=False):
        """Connect to SOAR using deprecated username and password method"""

        if include_permissions:
            LOG.debug("'include_permissions' is deprecated and scheduled to be removed in v50, use GET " +
                        "/rest/session/{org_id}/acl instead.\n\t\tAt that time, 'include_permissions' will be " +
                        "removed and this endpoint will not return org permissions.")

        # Wrap self.session.post and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __connect():
            r = self.session.post(u"{0}/rest/session?include_permissions={1}".format(self.base_url, "true" if include_permissions else "false"),
                                  data=json.dumps(self.authdata),
                                  proxies=self.proxies,
                                  headers=self.make_headers(),
                                  verify=self.verify,
                                  timeout=timeout,
                                  cert=self.cert)

            RetryHTTPException.raise_if_error(r)
            return r

        response = retry_call(__connect,
                              exceptions=(RetryHTTPException, ConnectionError),
                              tries=self.max_connection_retries,
                              delay=self.request_retry_delay,
                              backoff=self.request_retry_backoff)

        session = json.loads(response.text)
        self._extract_org_id(session)

        # set the X-sess-id token, which is used to prevent CSRF attacks.
        self.headers['X-sess-id'] = session['csrf_token']
        self.cookies = {
            'JSESSIONID': response.cookies['JSESSIONID']
        }
        self.user_id = session["user_id"]
        return session

    def make_headers(self, co3_context_token=None, additional_headers=None):
        """Makes a headers dict, including the X-Co3ContextToken (if co3_context_token is specified)."""
        headers = self.headers.copy()

        if co3_context_token is not None:
            headers['X-Co3ContextToken'] = co3_context_token
        if isinstance(additional_headers, dict):
            headers.update(additional_headers)
        return headers

    def _execute_request(self, operation, url, **kwargs):
        """
        If self.use_api_key is set to ``True``, set the ``auth`` header
        of the request to a ``HTTPBasicAuth`` using the api key id and secret

        Then execute the request

        :param operation: the requests.Session method to call
        :type operation: requests.Session.get | requests.Session.post | requests.Session.delete
        :param url: URL to send request to
        :type url: str
        :return: requests.response object
        :rtype: requests.response
        """

        if self.use_api_key:
            kwargs["auth"] = HTTPBasicAuth(self.api_key_id, self.api_key_secret)
            #
            #   Note this is a temporary walk around. Theoretically the server
            #   shall ignore the session id if api key is used. But we don't have
            #   time to do that yet. So we clear the session id here
            #
            self.session.cookies.clear()

        result = operation(url, **kwargs)

        return result

    def get(self, uri, co3_context_token=None, timeout=None, is_uri_absolute=None, get_response_object=None,
            skip_retry=[]):
        """Gets the specified URI.  Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So
        for example, if you specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
          is_uri_absolute: if True, does not insert /org/{org_id} into the uri
          get_response_object: if True, returns the response object rather than the json of the response.text
          skip_retry: list of HTTP responses to skip throwing an exception
        Returns:
          A dictionary, array, or response object with the value returned by the server.
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """

        if is_uri_absolute:
            url = u"{0}/rest{1}".format(self.base_url, ensure_unicode(uri))

        else:
            url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))

        # Wrap _execute_request and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __get():
            r = self._execute_request(self.session.get,
                                      url,
                                      proxies=self.proxies,
                                      cookies=self.cookies,
                                      headers=self.make_headers(co3_context_token),
                                      verify=self.verify,
                                      timeout=timeout,
                                      cert=self.cert)
            RetryHTTPException.raise_if_error(r, skip_retry=skip_retry)
            return r

        response = retry_call(__get,
                              exceptions=(RetryHTTPException, ConnectionError),
                              tries=self.request_max_retries,
                              delay=self.request_retry_delay,
                              backoff=self.request_retry_backoff)

        if get_response_object:
            return response

        return json.loads(response.text)

    def get_const(self, co3_context_token=None, timeout=None):
        """
        Get the ``ConstREST`` endpoint.

        Endpoint for retrieving various constant information for this server. This information is
        useful in translating names that the user sees to IDs that other REST API endpoints accept.

        For example, the ``incidentDTO`` has a field called ``"crimestatus_id"``. The valid values are stored
        in ``constDTO.crime_statuses``.

        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :return: ``ConstDTO`` as a dictionary
        :rtype: dict
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        url = u"{0}/rest/const".format(self.base_url)
        response = self._execute_request(self.session.get,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout,
                                         cert=self.cert)
        RetryHTTPException.raise_if_error(response)
        return response.json()

    def get_content(self, uri, co3_context_token=None, timeout=None, skip_retry=[]):
        """Gets the specified URI.  Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So
        for example, if you specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
          skip_retry: list of HTTP responses to skip throwing an exception
        Returns:
          The raw value returned by the server for this resource.
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        response = self._execute_request(self.session.get,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout,
                                         cert=self.cert)
        RetryHTTPException.raise_if_error(response, skip_retry=skip_retry)
        return response.content

    def post(self, uri, payload=None, co3_context_token=None, timeout=None, headers=None,
             skip_retry=[], is_uri_absolute=None, get_response_object=None, **kwargs):
        """
        Posts to the specified URI.
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you
        specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents
        Args:
           uri
           payload
           co3_context_token
           timeout: number of seconds to wait for response
           headers: optional headers to include
           skip_retry: list of HTTP responses to skip throwing an exception
           is_uri_absolute: if True, does not insert /org/{org_id} into the uri
           get_response_object: if True, returns the response object rather than the json of the response.text or response.content
           **kwargs: any other keyword-arguments to pass through to the ``requests.post()`` method
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """
        if is_uri_absolute:
            url = u"{0}/rest{1}".format(self.base_url, ensure_unicode(uri))
        else:
            url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))

        # payloads which aren't convertable to json are passed asis
        payload_json = json.dumps(payload) if isinstance(payload, (list, dict)) else payload

        #----
        # Wrap _execute_request and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __post():
            r = self._execute_request(self.session.post,
                                      url,
                                      data=payload_json,
                                      proxies=self.proxies,
                                      cookies=self.cookies,
                                      headers=self.make_headers(co3_context_token, additional_headers=headers),
                                      verify=self.verify,
                                      timeout=timeout,
                                      cert=self.cert,
                                      **kwargs)
            RetryHTTPException.raise_if_error(r, skip_retry=skip_retry)
            return r

        response = retry_call(__post,
                              exceptions=(RetryHTTPException, ConnectionError),
                              tries=self.request_max_retries,
                              delay=self.request_retry_delay,
                              backoff=self.request_retry_backoff)

        RetryHTTPException.raise_if_error(response, skip_retry=skip_retry)

        if get_response_object:
            return response
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            return response.content

    def post_attachment(self, uri, filepath,
                        filename=None,
                        mimetype=None,
                        data=None,
                        co3_context_token=None,
                        timeout=None,
                        bytes_handle=None,
                        skip_retry=[]):
        """
        Upload a file to the specified URI
        e.g. "/incidents/<id>/attachments" (for incident attachments)
        or,  "/tasks/<id>/attachments" (for task attachments)

        :param uri: The REST URI for posting
        :param filepath:the path of the file to post or if ``None``, use ``bytes_handle``
        :param filename: optional name of the file when posted
        :param mimetype: optional override for the guessed MIME type
        :param data: optional dict with additional MIME parts (not required for file attachments; used in artifacts)
        :param co3_context_token: Action Module context token, if responding to an Action Module event
        :param timeout: optional timeout (seconds)
        :param bytes_handle: BytesIO handle for content, used if ``filepath`` is None
        :param skip_retry: list of HTTP responses to skip throwing an exception
        """
        filepath = ensure_unicode(filepath)
        if filename:
            filename = ensure_unicode(filename)
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        mime_type = mimetype or mimetypes.guess_type(filename or filepath)[0] or "application/octet-stream"

        # Wrap _execute_request and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __post_attachment(name=None, file_or_bytes_handle=None, extra_data=None):
            multipart_data = {'file': (name, file_or_bytes_handle, mime_type)}
            multipart_data.update(extra_data or {})
            encoder = MultipartEncoder(fields=multipart_data)
            headers = self.make_headers(co3_context_token, additional_headers={'content-type': encoder.content_type})
            r = self._execute_request(self.session.post,
                                      url,
                                      data=encoder,
                                      proxies=self.proxies,
                                      cookies=self.cookies,
                                      headers=headers,
                                      verify=self.verify,
                                      timeout=timeout,
                                      cert=self.cert)
            RetryHTTPException.raise_if_error(r, skip_retry=skip_retry)
            return json.loads(r.text)

        if filepath:
            with open(filepath, 'rb') as file_handle:
                attachment_name = filename or os.path.basename(filepath)
                json_resp = retry_call(__post_attachment,
                                       fkwargs={
                                           "name": attachment_name,
                                           "file_or_bytes_handle": file_handle,
                                           "extra_data": data
                                       },
                                       exceptions=(RetryHTTPException, ConnectionError),
                                       tries=self.request_max_retries,
                                       delay=self.request_retry_delay,
                                       backoff=self.request_retry_backoff)
                return json_resp

        elif bytes_handle:
            attachment_name = filename if filename else "Unknown"
            json_resp = retry_call(__post_attachment,
                                   fkwargs={
                                       "name": attachment_name,
                                       "file_or_bytes_handle": bytes_handle,
                                       "extra_data": data
                                   },
                                   exceptions=(RetryHTTPException, ConnectionError),
                                   tries=self.request_max_retries,
                                   delay=self.request_retry_delay,
                                   backoff=self.request_retry_backoff)
            return json_resp

        else:
            raise ValueError("Either filepath or bytes_handle are required")

    def post_artifact_file(self, uri, artifact_type, artifact_filepath,
                           description=None,
                           value=None,
                           mimetype=None,
                           co3_context_token=None,
                           timeout=None,
                           bytes_handle=None,
                           skip_retry=[]):
        """
        Post a file artifact to the specified URI
        e.g. "/incidents/<id>/artifacts/files"

        :param uri: The REST URI for posting
        :param artifact_type: the artifact type name ("IP Address", etc) or type ID
        :param artifact_filepath: the path of the file to post or ``None`` if using ``bytes_handle``
        :param description: optional description for the artifact
        :param value: optional value for the artifact
        :param mimetype: optional override for the guessed MIME type
        :param co3_context_token: Action Module context token, if responding to an Action Module event
        :param timeout: optional timeout (seconds)
        :param bytes_handle: byte content to create as an artifact file, used if ``artifact_filepath`` is ``None``
        :param skip_retry: list of HTTP responses to skip throwing an exception
        """
        artifact = {
            "type": artifact_type,
            "value": value or "",
            "description": description or ""
        }
        mimedata = {
            "artifact": json.dumps(artifact)
        }
        return self.post_attachment(uri,
                                    artifact_filepath,
                                    filename=value if bytes_handle else None,
                                    mimetype=mimetype,
                                    data=mimedata,
                                    co3_context_token=co3_context_token,
                                    timeout=timeout,
                                    bytes_handle=bytes_handle)

    def _get_put(self, uri, apply_func, co3_context_token=None, timeout=None, skip_retry=[]):
        """Internal helper to do a get/apply/put loop
        (for situations where the put might return a 409/conflict status code)
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        response = self._execute_request(self.session.get,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout,
                                         cert=self.cert)
        RetryHTTPException.raise_if_error(response, skip_retry=skip_retry)
        payload = json.loads(response.text)
        try:
            apply_func(payload)
        except NoChange:
            return payload
        payload_json = json.dumps(payload)
        response = self._execute_request(self.session.put,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout,
                                         cert=self.cert)
        if response.status_code == 200:
            return json.loads(response.text)
        if response.status_code == 409:
            return None
        RetryHTTPException.raise_if_error(response, skip_retry=skip_retry)
        return None

    def get_put(self, uri, apply_func, co3_context_token=None, timeout=None):
        """Performs a get, calls apply_func on the returned value, then calls self.put.
        If the put call returns a 409 error, then retry.

        Args:
          uri - the URI to use.  Note that this is expected to be relative to the org.
          apply_func - a function to call on the object returned by get.  This is expected
          to alter the object with the desired changes.
          co3_context_token - the Co3ContextToken from a CAF message (if the caller is
          a CAF message processor.
          timeout - number of seconds to wait for response
        Returns;
          The object returned by the put operation (converted from JSON to a Python dict).
        Raises:
          Exception if the get or put returns an unexpected status code.
        """
        while True:
            obj = self._get_put(uri, apply_func, co3_context_token=co3_context_token, timeout=timeout)
            if obj:
                return obj
        return None

    def put(self, uri, payload, co3_context_token=None, timeout=None, headers=None,
            skip_retry=[]):
        """
        Puts to the specified URI.
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you
        specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents
        Args:
           uri
           payload
           headers: optional headers to include
           co3_context_token
           timeout: number of seconds to wait for response
           skip_retry: list of HTTP responses to skip throwing an exception
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        # payloads which aren't convertable to json are passed asis
        payload_json = json.dumps(payload) if isinstance(payload, (list, dict)) else payload
        response = self._execute_request(self.session.put,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token, additional_headers=headers),
                                         verify=self.verify,
                                         timeout=timeout,
                                         cert=self.cert)
        RetryHTTPException.raise_if_error(response, skip_retry=skip_retry)
        return json.loads(response.text)

    def delete(self, uri, co3_context_token=None, timeout=None, skip_retry=[]):
        """Deletes the specified URI.

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
          skip_retry: list of HTTP responses to skip throwing an exception
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          RetryHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))

        # Wrap _execute_request and its related raise_if_error call in
        # inner function so we can add retry logic with dynamic parameters to it
        def __delete():
            r = self._execute_request(self.session.delete,
                                      url,
                                      proxies=self.proxies,
                                      cookies=self.cookies,
                                      headers=self.make_headers(co3_context_token),
                                      verify=self.verify,
                                      timeout=timeout,
                                      cert=self.cert)
            if r.status_code == 204:
                # 204 - No content is OK for a delete
                return None

            RetryHTTPException.raise_if_error(r, skip_retry=skip_retry)
            return json.loads(r.text)

        response = retry_call(__delete,
                              exceptions=(RetryHTTPException, ConnectionError),
                              tries=self.request_max_retries,
                              delay=self.request_retry_delay,
                              backoff=self.request_retry_backoff)

        return response
