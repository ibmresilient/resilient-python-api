#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Simple client for Resilient REST API"""
import datetime
import importlib
import json
import logging
import os
import sys
from argparse import Namespace

import requests
from cachetools import TTLCache, cachedmethod

from . import co3base
from .co3base import NoChange, ensure_unicode, get_proxy_dict
from .patch import PatchStatus

try:
    # Python 3
    import urllib.parse as urlparse
except:
    # Python 2
    import urlparse


DEFAULT_CONFIG_FILENAME = "app.config"
LOG = logging.getLogger(__name__)


def get_resilient_circuits_version():
    """
    If resilient-circuits is installed, returns its version
    Else will return None
    """
    try:
        import resilient_circuits
        res_circuits_version = resilient_circuits.__version__.split(".")
        return {
            "major": int(res_circuits_version[0]),
            "minor": int(res_circuits_version[1]),
            "patch": int(res_circuits_version[2])
        }

    except ImportError:
        pass

    return None


def get_config_file(filename=None, generate_filename=False):
    """
    Helper: get the location of the configuration file
    * Use the location specified in $APP_CONFIG_FILE, if set
    * Otherwise if filename path specified in args exist in the current working use as config file.
    * Otherwise if default config file name exists in current work directory use as config file.
    * Otherwise use path in ~/.resilient/ directory

    :param filename: The filename to use for the app config file.
    :param generate_filename: Boolean is used for config filename generation.
    """
    # The config file location should usually be set in the environment
    # First check environment, then cwd, then ~/.resilient/app.config
    env_app_config_file = os.environ.get("APP_CONFIG_FILE", None)

    if not env_app_config_file:
        if generate_filename and filename:
            # If generating the config file and filename passed in, use it as the config file name.
            config_file = os.path.expandvars(os.path.expanduser(filename))
        else:
            if not filename:
                # If file not specified use default value.
                filename = DEFAULT_CONFIG_FILENAME
            # If the filename exists in local directory use as config file name.
            if not generate_filename and os.path.exists(filename):
                config_file = filename
            else:
                # Use default config file in ~/.resilient/app.config.
                config_file = os.path.expanduser(os.path.join("~", ".resilient", filename))
                if generate_filename:
                    # If generating the config file location, create the '~/.resilient' directory if missing.
                    resilient_dir = os.path.dirname(config_file)
                    if not os.path.exists(resilient_dir):
                        LOG.info(u"Creating %s", resilient_dir)
                        os.makedirs(resilient_dir)
    else:
        config_file = env_app_config_file
    return config_file


def get_client(opts, custom_headers=None, **kwargs):
    """
    This is a helper method to get an instance of
    :class:`SimpleClient` for the SOAR REST API.

    :param opts: the connection options - usually the contents of the app.config file
    :type opts: dict
    :param custom_headers: A dictionary of any headers you want to send in **every** request
    :type custom_headers: dict
    :param kwargs: A dictionary of any other keyword arguments
    :type kwargs: dict

    A standard way to initialize a :class:`SimpleClient` with default configuration is:

    .. code-block:: python

        parser = resilient.ArgumentParser(config_file=resilient.get_config_file())
        opts = parser.parse_args()
        client = resilient.get_client(opts)

    :return: a connected and verified instance of :class:`SimpleClient`
    """
    if isinstance(opts, Namespace):
        opts = vars(opts)

    # Allow explicit setting "do not verify certificates"
    verify = opts.get("cafile")
    if str(verify).lower() == "false":
        LOG.warning("Unverified HTTPS requests (cafile=false).")
        requests.packages.urllib3.disable_warnings()  # otherwise things get very noisy
        verify = False

    # Enable client certificate authentication
    clientauthcert = opts.get("client_auth_cert", None)
    clientauthkey = opts.get("client_auth_key", None)
    certauth = (clientauthcert, clientauthkey)
    if str(clientauthcert).lower() == "false" or clientauthcert is None or clientauthkey is None:
        certauth = False

    proxy = None
    if opts.get("proxy_host"):
        proxy = get_proxy_dict(opts)

    # Create SimpleClient for a REST connection to the Resilient services
    url = "https://{0}:{1}".format(opts.get("host", ""), opts.get("port", 443))
    url = urlparse.urljoin(url, opts.get("resource_prefix", ""))
    simple_client_args = {"org_name": opts.get("org"),
                          "proxies": proxy,
                          "base_url": url,
                          "verify": verify,
                          "certauth": certauth,
                          "custom_headers": custom_headers}
    if opts.get("log_http_responses"):
        LOG.warning("Logging all HTTP Responses from Resilient to %s", opts["log_http_responses"])
        simple_client = LoggingSimpleClient
        simple_client_args["logging_directory"] = opts["log_http_responses"]
    else:
        simple_client = SimpleClient

    # Update with kwargs
    simple_client_args.update(kwargs)

    resilient_client = simple_client(**simple_client_args)

    if opts.get("resilient_mock"):
        # Use a Mock for the Resilient Rest API
        LOG.warning("Using Mock '%s' for Resilient REST API", opts["resilient_mock"])
        module_path, class_name = opts["resilient_mock"].rsplit('.', 1)
        path, module_name = os.path.split(module_path)
        sys.path.insert(0, path)
        module = importlib.import_module(module_name)
        LOG.info("Looking for %s in %s", class_name, dir(module))
        mock_class = getattr(module, class_name)
        res_mock = mock_class(org_name=opts.get("org"), email=opts["email"])
        resilient_client.session.mount("https://", res_mock.adapter)

    #
    #   Check if we are using API Key or user/password. API key is the
    #   preferable one if we can find from the opts
    #
    if opts.get("api_key_id", None) is not None and opts.get("api_key_secret", None) is not None:
        userinfo = resilient_client.set_api_key(api_key_id=opts["api_key_id"],
                                                api_key_secret=opts["api_key_secret"])
    else:
        userinfo = resilient_client.connect(opts["email"], opts["password"])

    # Validate the org, and store org_id in the opts dictionary
    LOG.debug(json.dumps(userinfo, indent=2))
    if(len(userinfo["orgs"])) > 1 and opts.get("org") is None:
        raise Exception("User is a member of multiple organizations; please specify one.")
    if(len(userinfo["orgs"])) > 1:
        for org in userinfo["orgs"]:
            if org["name"] == opts.get("org"):
                opts["org_id"] = org["id"]
    else:
        opts["org_id"] = userinfo["orgs"][0]["id"]

    # Check if action module is enabled and store to opts dictionary
    org_data = resilient_client.get('')
    resilient_client.actions_enabled = org_data["actions_framework_enabled"]

    return resilient_client


class SimpleHTTPException(Exception):
    """Exception for HTTP errors."""
    def __init__(self, response):
        """
        :param response: The Response object from the get/put/etc.
        """
        super(SimpleHTTPException, self).__init__(u"{0}:  {1}".format(response.reason, response.text))

        self.response = response


class PatchConflictException(SimpleHTTPException):
    """Exception for patch conflicts."""
    def __init__(self, response, patch_status):
        super(PatchConflictException, self).__init__(response)

        self.patch_status = patch_status


def _raise_if_error(response):
    """Helper to raise a SimpleHTTPException if the response.status_code is not 200.

    :param response: the Response object from a get/put/etc.
    :raises SimpleHTTPException: if response.status_code is not 200.
    """
    if response.status_code != 200:
        raise SimpleHTTPException(response)


class SimpleClient(co3base.BaseClient):
    """
    Python helper class for using the IBM SOAR REST API.

    .. code-block::

        '''
        An example script showing how to connect and get
        incidents with IBM Security SOAR

        Example Usage:
        python sample_connect.py "https://<host>", "<org_name>", "<api_key_id>", "<api_key_secret>", "<path_to_ca_file>|False"
        '''

        import sys
        import os
        from resilient import SimpleClient


        def main():

            args = sys.argv
            assert len(args) == 6
            SCRIPT_NAME = args[0]

            # Get required parameters
            HOST = args[1]
            ORG_NAME = args[2]
            API_KEY_ID = args[3]
            API_KEY_SECRET = args[4]

            # Check if using cafile
            ca_file = args[5]
            VERIFY = ca_file if os.path.isfile(ca_file) is True else False

            # Instansiate SimpleClient
            res_client = SimpleClient(
                org_name=ORG_NAME,
                base_url=HOST,
                verify=VERIFY
            )

            # Set the API Key
            res_client.set_api_key(
                api_key_id=API_KEY_ID,
                api_key_secret=API_KEY_SECRET
            )

            # Setup the request payload
            payload = {
                "filters": [
                    {
                        "conditions": [{"field_name": "plan_status", "method": "equals", "value": "A"}]
                    }
                ]
            }

            # Invoke the request
            response = res_client.post("/incidents/query_paged?return_level=full", payload=payload)

            # Print results
            for incident in response.get("data", []):
                print("{0}: {1}".format(incident.get("id"), incident.get("name")))


        if __name__ == "__main__":
            main()


    .. note::
        The full REST API Documentation for IBM SOAR can be
        viewed on the Platform itself by searching for the **REST API Reference**
        or by going to: ``https://<base_url>/docs/rest-api/index.html``
    """

    def __init__(self, org_name=None, base_url=None, proxies=None, verify=None, cache_ttl=240, certauth=None, custom_headers=None, **kwargs):
        """
        :param org_name: The name of the organization to use.
        :type org_name: str
        :param base_url: The base URL of the SOAR server, e.g. ``https://soar.ibm.com/``
        :type base_url: str
        :param proxies: A dictionary of ``HTTP`` proxies to use, if any.
        :type proxies: dict
        :param verify: The path to a ``PEM`` file containing the trusted CAs, or ``False`` to disable all TLS verification
        :type verify: str|bool
        :param cache_ttl: Time in seconds to live for cached API responses
        :type cache_ttl: int
        :param certauth: The filepath for the client side certificate and the private key either as a single file or as a tuple of both files' paths
        :type certauth: str|tuple(str, str)
        :param custom_headers: A dictionary of any headers you want to send in **every** request
        :type custom_headers: dict
        :param kwargs: A dictionary of any other keyword arguments including;

            * **max_connection_retries** (*int*) - Number of attempts to retry when connecting to SOAR. Use ``-1`` for unlimited retries. Defaults to ``-1``.
            * **request_max_retries** (*int*) - Max number of times to retry a request to SOAR before exiting. Defaults to ``5``.
            * **request_retry_delay** (*int*) - Number of seconds to wait between retries. Defaults to ``2``.
            * **request_retry_backoff** (*int*) - Multiplier applied to delay between retry attempts. Defaults to ``2``.

        :type kwargs: dict
        """
        super(SimpleClient, self).__init__(org_name, base_url, proxies, verify, certauth, custom_headers=custom_headers, **kwargs)
        self.cache = TTLCache(maxsize=128, ttl=cache_ttl)

    def connect(self, email, password, timeout=None):
        """
        Connect and authenticate to the IBM SOAR REST API service.

        :param email: The email address to use for authentication.
        :type email: str
        :param password: The password.
        :type password: str
        :param timeout: optional timeout (seconds)
        :type timeout: int
        :return: The IBM SOAR session object.
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Calling connect of BaseClient. Convert the exception if there is any
        ret = None
        try:
            ret = super(SimpleClient, self).connect(email, password, timeout)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())

        return ret

    def __make_headers(self, co3_context_token=None, additional_headers=None):
        return self.make_headers(co3_context_token, additional_headers)

    def _keyfunc(self, uri, *args, **kwargs):
        """ function to generate cache key for cached_get """
        return uri

    def _get_cache(self):
        return self.cache

    def get(self, uri, co3_context_token=None, timeout=None, is_uri_absolute=None, get_response_object=None, skip_retry=[]):
        """Gets the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to fetch.
        :type uri: str
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param is_uri_absolute: if True, does not insert /org/{org_id} into the uri.
        :type is_uri_absolute: bool
        :param get_response_object: if True, returns entire response object.
        :type get_response_object: bool
        :return: A dictionary, list, or response object with the value returned by the server.
        :rtype: dict | list | Response
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call get from BaseClient, convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).get(uri, co3_context_token, timeout, is_uri_absolute, get_response_object, skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    @cachedmethod(_get_cache, key=_keyfunc)
    def cached_get(self, uri, co3_context_token=None, timeout=None, skip_retry=[]):
        """ Same as :meth:`get()`, but checks cache first """
        return self.get(uri, co3_context_token, timeout, skip_retry=skip_retry)

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
        # Call get_const from BaseClient. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).get_const(co3_context_token, timeout)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    def get_content(self, uri, co3_context_token=None, timeout=None, skip_retry=[]):
        """Gets the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to fetch.
        :type uri: str
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :return: The raw value returned by the server for this resource.
        :rtype: dict
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call get_content from BaseClient. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).get_content(uri, co3_context_token, timeout, skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    def post(self, uri, payload, co3_context_token=None, timeout=None, headers=None, skip_retry=[], **kwargs):
        """
        Posts to the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to post.
        :type uri: str
        :param payload: A dictionary value to be posted.
        :type payload: dict
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param headers: Optional headers to include.
        :type headers: dict
        :return: A dictionary or list with the value returned by the server.
        :rtype: dict | list
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call post of BaseClient. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).post(uri, payload, co3_context_token, timeout, headers=headers, skip_retry=skip_retry, **kwargs)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    def _patch(self, uri, patch, co3_context_token=None, timeout=None):
        """Internal method used to call the underlying server patch endpoint"""
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        if isinstance(patch, dict):
            payload_json = json.dumps(patch)
        else:
            payload_json = json.dumps(patch.to_dict())

        hdrs = {"handle_format": "names"}
        response = self._execute_request(self.session.patch,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token,
                                                                   additional_headers=hdrs),
                                         verify=self.verify,
                                         timeout=timeout)

        return response

    def _handle_patch_response(self, response, patch, callback):
        """Helper to determine if a patch retry is needed.  Will only return True if the server responds with a
        409 or if the patch apply failed with field failures and the caller asked to overwrite conflicts."""
        if response.status_code == 409:
            # Just retry again, no adjustments.  The server can return 409 if there is a DB-level conflict.
            LOG.info("Retrying patch unchanged due to server CONFLICT")
            return True

        if response.status_code == 200:
            json = response.json()

            LOG.debug(json)

            patch_status = PatchStatus(json)

            if not patch_status.is_success() and patch_status.has_field_failures():
                LOG.info("Patch conflict detected - invoking callback")

                before = patch.get_old_values()

                try:
                    callback(response, patch_status, patch)
                except NoChange:
                    # Callback explicitly indicated that it didn't want to apply the change, so just
                    # return False here to stop processing.
                    #
                    LOG.debug("callback indicated no change after conflict - skipping")
                    return False

                if not patch.has_changes():
                    LOG.debug("callback removed all conflicts from patch - no need to re-issue")
                    return False

                # Make sure something in the patch has actually changed, otherwise we'd
                # just re-issue the same patch and get into a loop.
                after = patch.get_old_values()

                if before == after:
                    raise ValueError("invoked callback did not change the patch object, but returned True")

                return True

        # Raise an exception if there's some non-200 response.
        _raise_if_error(response)

        # Don't want to retry and got a 200 response.  There may or may not be field_failures.
        # Handling that is now up to the caller of the patch method.
        return False

    @staticmethod
    def _patch_overwrite_callback(response, patch_status, patch):
        """
        Callback to use when the caller specified overwrite_conflict=True in the patch call.
        """
        patch.update_for_overwrite(patch_status)

    @staticmethod
    def _patch_raise_callback(response, patch_status, patch):
        """
        Callback to use when the caller specified overwrite_conflict=False in the patch call.
        """
        # Got a conflict and no callback specified.  Just raise an exception.
        raise PatchConflictException(response, patch_status)

    def patch(self, uri, patch, co3_context_token=None, timeout=None, overwrite_conflict=False):
        """
        PATCH request to the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to patch.
        :type uri: str
        :param patch: The :class:`~resilient.patch.Patch` object to apply
        :type patch: :class:`~resilient.patch.Patch`
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param overwrite_conflict: always overwrite fields in conflict. If ``True``, the passed-in patch
            object will be modified if necessary.
        :type overwrite_conflict: bool
        :return: the ``response`` from the endpoint.
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_
        :raises SimpleHTTPException: if an HTTP exception or patch conflict occurs.
        :raises PatchConflictException: If the patch failed to apply (and overwrite_conflict is False).
        """
        if overwrite_conflict:
            # Re-issue patch with intent to overwrite conflicts.
            callback = SimpleClient._patch_overwrite_callback
        else:
            # Raise an exception on conflict.
            callback = SimpleClient._patch_raise_callback

        return self.patch_with_callback(uri, patch, callback, co3_context_token, timeout)

    def patch_with_callback(self, uri, patch, callback, co3_context_token=None, timeout=None):
        """
        PATCH request to the specified URI.  If the patch application fails because of field conflicts,
        the specified callback is invoked, allowing the caller to adjust the patch as necessary.

        :param uri: Relative URI of the resource to patch.
        :type str: Relative URI of the resource to patch.
        :param patch: The :class:`~resilient.patch.Patch` object to apply
        :type patch: :class:`~resilient.patch.Patch`
        :param callback: Function/lambda to invoke when a patch conflict is detected.  The function/lambda must be
          of the following form: ``def my_callback(response, patch_status, patch)``.
          If your callback raises :class:`resilient.NoChange <resilient.co3base.NoChange>`, the update is skipped.
        :type callback: func
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :return: the ``response`` from the endpoint.
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_
        """
        response = self._patch(uri, patch, co3_context_token, timeout)

        while self._handle_patch_response(response, patch, callback):
            response = self._patch(uri, patch, co3_context_token, timeout)

        return response

    def post_attachment(self, uri, filepath, filename=None,
                        mimetype=None, data=None, co3_context_token=None, timeout=None,
                        bytes_handle=None, skip_retry=[]):
        """
        Upload a file to the specified URI
        e.g. ``/incidents/<id>/attachments`` (for incident attachments)
        or ``/tasks/<id>/attachments`` (for task attachments)

        .. warning::
            Please see our updated :class:`resilient_lib.write_file_attachment <resilient_lib.components.resilient_common.write_file_attachment>`
            as this method takes a data stream and is more reliable

        :param uri: Relative URI of the resource to post.
        :type uri: str
        :param filepath: the path of the file to post
        :type filepath: str
        :param filename: optional name of the file when posted
        :type filename: str
        :param mimetype: optional override for the guessed MIME type
        :type mimetype: str
        :param data: optional dict with additional ``MIME`` parts (not required for file attachments; used in artifacts)
        :type data: dict
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param bytes_handle: BytesIO handle for content or use filepath
        :type bytes_handle: BytesIO
        :return: the ``response`` from the endpoint.
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_
        """
        # Call BaseClient post_attachment. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).post_attachment(uri, filepath, filename=filename,
                                                                 mimetype=mimetype,
                                                                 data=data,
                                                                 co3_context_token=co3_context_token,
                                                                 timeout=timeout,
                                                                 bytes_handle=bytes_handle,
                                                                 skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    def search(self, payload, co3_context_token=None, timeout=None):
        """
        Posts to the ``SearchExREST`` endpoint.

        Endpoint for performing full text searches through incidents and incident child objects
        (tasks, incident comments, task comments, milestones, artifacts, incident attachments,
        task attachments, and data tables).

        :param payload: The SearchExInputDTO parameters for performing a search.
        :type payload: dict
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :return: List of results, as an array of ``SearchExResultDTO``
        :rtype: list
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        url = u"{0}/rest/search_ex".format(self.base_url)
        payload_json = json.dumps(payload)
        response = self._execute_request(self.session.post,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        _raise_if_error(response)
        return json.loads(response.text)

    def get_put(self, uri, apply_func, co3_context_token=None, timeout=None, skip_retry=[]):
        """
        Safely performs an update operation by a GET, calls your ``apply_func`` callback, then PUT
        with the updated value.  If the put call returns a ``409`` error, these steps are retried.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to get and update.
        :type uri: str
        :param apply_func: A callback function that you implement to update the resource.  The function must be
          of the following form: ``def my_apply_func(object_to_update)``, and update the object.
          If your callback raises :class:`resilient.NoChange <resilient.co3base.NoChange>`, the update is skipped.
        :type apply_func: func
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param skip_retry: list of HTTP responses to skip throwing an exception
        :type skip_retry: list
        :return: A dictionary or list with the value returned by the PUT operation.
        :rtype: dict | list
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call BaseClient get_put. Convert exception if there is any
        res = None
        try:
            res = super(SimpleClient, self).get_put(uri, apply_func, co3_context_token, timeout, skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return res

    def put(self, uri, payload, co3_context_token=None, timeout=None, headers=None, skip_retry=[]):
        """
        Directly performs an update operation by PUT to the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``


        :param uri: Relative URI of the resource to update.
        :type uri: str
        :param payload: The object to update.
        :type payload: dict
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :param headers: Optional headers to include.
        :type headers: dict
        :return: A dictionary or list with the value returned by the server.
        :rtype: dict | list
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call BaseClient put. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).put(uri, payload, co3_context_token, timeout, headers=headers, skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response

    def delete(self, uri, co3_context_token=None, timeout=None, skip_retry=[]):
        """
        Deletes the specified URI.

        .. note::
            This URI is relative to ``<base_url>/rest/orgs/<org_id>``.  So for example,
            if you specify a uri of ``/incidents``, the actual URL would be something like:
            ``https://soar.ibm.com/rest/orgs/201/incidents``

        :param uri: Relative URI of the resource to delete.
        :type uri: str
        :param co3_context_token: The ``Co3ContextToken`` from an Action Module message, if available.
        :type co3_context_token: str
        :param timeout: Optional timeout (seconds).
        :type timeout: int
        :raises SimpleHTTPException: if an HTTP exception occurs.
        """
        # Call BaseClient delete. Convert exception if there is any
        response = None
        try:
            response = super(SimpleClient, self).delete(uri, co3_context_token, timeout, skip_retry=skip_retry)
        except co3base.BasicHTTPException as ex:
            _raise_if_error(ex.get_response())
        return response


class LoggingSimpleClient(SimpleClient):
    """ Simple Client version that logs all Resilient REST API responses to disk.  Useful when building a Mock."""
    def __init__(self, logging_directory="", *args, **kwargs):
        super(LoggingSimpleClient, self).__init__(*args, **kwargs)
        try:
            directory = os.path.expanduser(logging_directory)
            directory = os.path.expandvars(directory)
            assert(os.path.exists(directory))
            self.logging_directory = directory
        except Exception as e:
            raise Exception("Response Logging Directory %s does not exist!",
                            logging_directory)

    def _log_response(self, response, *args, **kwargs):
        """ Log Headers and JSON from a Requests Response object """
        url = urlparse.urlparse(response.url)
        filename = "_".join((str(response.status_code), "{0}",
                             response.request.method,
                             url.path, url.params,
                             datetime.datetime.now().isoformat())).replace('/', '_').replace(':', '-')
        try:
            with open(os.path.join(self.logging_directory,
                                   filename.format("JSON")), "w+") as logfile:
                logfile.write(json.dumps(response.json(), indent=2))
        except:
            with open(os.path.join(self.logging_directory,
                                   filename.format("DATA")), "w+b") as logfile:
                logfile.write(response.content)
        with open(os.path.join(self.logging_directory,
                               filename.format("HEADER")), "w+") as logfile:
            logfile.write(json.dumps(dict(response.headers), indent=2))

    def _connect(self, *args, **kwargs):
        """ Connect to Resilient and log response """
        normal_post = self.session.post
        self.session.post = lambda *args, **kwargs: normal_post(
            hooks=dict(response=self._log_response), *args, **kwargs)
        session = super(LoggingSimpleClient, self)._connect(*args, **kwargs)
        self.session.post = normal_post
        return session

    def _execute_request(self, operation, url, **kwargs):
        """Execute a HTTP request and log response.
           If unauthorized (likely due to a session timeout), retry.
        """
        def wrapped_operation(url, **kwargs):
            return operation(url, hooks=dict(response=self._log_response),
                             **kwargs)
        return super(LoggingSimpleClient, self)._execute_request(
            wrapped_operation, url, **kwargs)
