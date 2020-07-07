# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Base client for Resilient REST API"""
from __future__ import print_function

import json
import ssl
import mimetypes
import os
import sys
import logging
import unicodedata
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests_toolbelt.multipart.encoder import MultipartEncoder
from requests.auth import HTTPBasicAuth

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
    Despite the name, SSLv23 can select "TLS" protocols as well as "SSL".
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_SSLv23)


class BasicHTTPException(Exception):
    """Exception for HTTP errors."""
    def __init__(self, response):
        """
        Args:
          response - the Response object from the get/put/etc.
        """
        super(BasicHTTPException, self).__init__(u"{0}:  {1}".format(response.reason, response.text))

        self.response = response

    def get_response(self):
        return self.response

    @staticmethod
    def raise_if_error(response):
        if response.status_code != 200:
            raise BasicHTTPException(response)


class NoChange(Exception):
    """Exception that can be raised within a get/put handler or a patch callback
       to indicate 'no change' (which then just bypasses the update operation).
    """
    pass


def ensure_unicode(input_value):
    """ if input_value is type str, convert to unicode with utf-8 encoding """
    if sys.version_info.major >= 3:
        return input_value

    if not isinstance(input_value, basestring):
        return input_value
    elif isinstance(input_value, str):
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
    """Helper for using Resilient REST API."""

    def __init__(self, org_name=None, base_url=None, proxies=None, verify=None):
        """
        Args:
          org_name - the name of the organization to use.
          base_url - the base URL to use.
          proxies - HTTP proxies to use, if any.
          verify - The name of a PEM file to use as the list of trusted CAs.
        """
        self.headers = {'content-type': 'application/json'}
        self.cookies = None
        self.org_id = None
        self.user_id = None
        self.base_url = u'https://app.resilientsystems.com/'
        self.org_name = ensure_unicode(org_name)
        if proxies:
            self.proxies = {ensure_unicode(key): ensure_unicode(proxies[key]) for key in proxies}
        else:
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

    def set_api_key(self, api_key_id, api_key_secret, timeout=None):
        """
        Call this method instead of the connect method in order to use API key
        Just like the connect method, this method calls the session endpoint
        to get org_id information.
        :param api_key_id:
        :param api_key_secret:
        :return:
        """
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.use_api_key = True

        response = self.session.get(u"{0}/rest/session".format(self.base_url),
                                    auth=HTTPBasicAuth(self.api_key_id, self.api_key_secret),
                                    proxies=self.proxies,
                                    headers=self.make_headers(),
                                    verify=self.verify,
                                    timeout=timeout)
        BasicHTTPException.raise_if_error(response)
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
          BasicHTTPException - if an HTTP exception occurs.
        """
        self.authdata = {
            u'email': ensure_unicode(email),
            u'password': ensure_unicode(password)
        }
        return self._connect(timeout=timeout)

    def _extract_org_id(self, resp):
        """
        Extract org id from server resp
        :param resp: server response from session endpoint
        :return:
        """
        orgs = resp['orgs']
        selected_org = None
        if orgs is None or len(orgs) == 0:
            raise Exception("User is a member of no orgs")
        elif self.org_name:
            org_names = []
            for org in orgs:
                org_name = org['name']
                org_names.append(org_name)
                if ensure_unicode(org_name) == self.org_name:
                    selected_org = org
        else:
            org_names = [org['name'] for org in orgs]
            msg = u"Please specify the organization name to which you want to connect.  " + \
                  u"The user is a member of the following organizations: '{0}'"
            raise Exception(msg.format(u"', '".join(org_names)))

        if selected_org is None:
            msg = u"The user is not a member of the specified organization '{0}'."
            raise Exception(msg.format(self.org_name))

        if not selected_org.get("enabled", False):
            msg = "This organization is not accessible to you.\n\n" \
                  "This can occur because of one of the following:\n\n" \
                  "The organization does not allow access from your current IP address.\n" \
                  "The organization requires authentication with a different provider than you are currently using.\n" \
                  "Your IP address is {0}"
            raise Exception(msg.format(resp["session_ip"]))

        self.all_orgs = [org for org in orgs if org.get("enabled")]
        self.org_id = selected_org['id']

    def _connect(self, timeout=None):
        """Establish a session"""
        response = self.session.post(u"{0}/rest/session".format(self.base_url),
                                     data=json.dumps(self.authdata),
                                     proxies=self.proxies,
                                     headers=self.make_headers(),
                                     verify=self.verify,
                                     timeout=timeout)
        BasicHTTPException.raise_if_error(response)
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
        """Execute a HTTP request.
           If unauthorized (likely due to a session timeout), retry.
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
        if result.status_code == 401 and not self.use_api_key:  # unauthorized, re-auth and try again
            self._connect()
            result = operation(url, **kwargs)
        return result

    def get(self, uri, co3_context_token=None, timeout=None):
        """Gets the specified URI.  Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So
        for example, if you specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          BasicHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        response = self._execute_request(self.session.get,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        BasicHTTPException.raise_if_error(response)
        return json.loads(response.text)

    def get_content(self, uri, co3_context_token=None, timeout=None):
        """Gets the specified URI.  Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So
        for example, if you specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
        Returns:
          The raw value returned by the server for this resource.
        Raises:
          BasicHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        response = self._execute_request(self.session.get,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        BasicHTTPException.raise_if_error(response)
        return response.content

    def post(self, uri, payload, co3_context_token=None, timeout=None):
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
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          BasicHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        payload_json = json.dumps(payload)
        response = self._execute_request(self.session.post,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        BasicHTTPException.raise_if_error(response)
        return json.loads(response.text)

    def post_attachment(self, uri, filepath,
                        filename=None, mimetype=None, data=None, co3_context_token=None, timeout=None):
        """
        Upload a file to the specified URI
        e.g. "/incidents/<id>/attachments" (for incident attachments)
        or,  "/tasks/<id>/attachments" (for task attachments)

        :param uri: The REST URI for posting
        :param filepath: the path of the file to post
        :param filename: optional name of the file when posted
        :param mimetype: optional override for the guessed MIME type
        :param data: optional dict with additional MIME parts (not required for file attachments; used in artifacts)
        :param co3_context_token: Action Module context token, if responding to an Action Module event
        :param timeout: optional timeout (seconds)
        """
        filepath = ensure_unicode(filepath)
        if filename:
            filename = ensure_unicode(filename)
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        mime_type = mimetype or mimetypes.guess_type(filename or filepath)[0] or "application/octet-stream"
        with open(filepath, 'rb') as filehandle:
            attachment_name = filename or os.path.basename(filepath)
            multipart_data = {'file': (attachment_name, filehandle, mime_type)}
            multipart_data.update(data or {})
            encoder = MultipartEncoder(fields=multipart_data)
            headers = self.make_headers(co3_context_token,
                                        additional_headers={'content-type': encoder.content_type})
            response = self._execute_request(self.session.post,
                                             url,
                                             data=encoder,
                                             proxies=self.proxies,
                                             cookies=self.cookies,
                                             headers=headers,
                                             verify=self.verify,
                                             timeout=timeout)
            BasicHTTPException.raise_if_error(response)
            return json.loads(response.text)

    def post_artifact_file(self, uri, artifact_type, artifact_filepath,
                           description=None, value=None, mimetype=None, co3_context_token=None, timeout=None):
        """
        Post a file artifact to the specified URI
        e.g. "/incidents/<id>/artifacts/files"

        :param uri: The REST URI for posting
        :param artifact_type: the artifact type name ("IP Address", etc) or type ID
        :param artifact_filepath: the path of the file to post
        :param description: optional description for the artifact
        :param value: optional value for the artifact
        :param mimetype: optional override for the guessed MIME type
        :param co3_context_token: Action Module context token, if responding to an Action Module event
        :param timeout: optional timeout (seconds)

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
                                    mimetype=mimetype,
                                    data=mimedata,
                                    co3_context_token=co3_context_token,
                                    timeout=timeout)

    def _get_put(self, uri, apply_func, co3_context_token=None, timeout=None):
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
                                         timeout=timeout)
        BasicHTTPException.raise_if_error(response)
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
                                         timeout=timeout)
        if response.status_code == 200:
            return json.loads(response.text)
        elif response.status_code == 409:
            return None
        BasicHTTPException.raise_if_error(response)
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

    def put(self, uri, payload, co3_context_token=None, timeout=None):
        """
        Puts to the specified URI.
        Note that this URI is relative to <base_url>/rest/orgs/<org_id>.  So for example, if you
        specify a uri of /incidents, the actual URL would be something like this:

            https://app.resilientsystems.com/rest/orgs/201/incidents
        Args:
           uri
           payload
           co3_context_token
          timeout: number of seconds to wait for response
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          BasicHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        payload_json = json.dumps(payload)
        response = self._execute_request(self.session.put,
                                         url,
                                         data=payload_json,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        BasicHTTPException.raise_if_error(response)
        return json.loads(response.text)

    def delete(self, uri, co3_context_token=None, timeout=None):
        """Deletes the specified URI.

        Args:
          uri
          co3_context_token
          timeout: number of seconds to wait for response
        Returns:
          A dictionary or array with the value returned by the server.
        Raises:
          BasicHTTPException - if an HTTP exception occurs.
        """
        url = u"{0}/rest/orgs/{1}{2}".format(self.base_url, self.org_id, ensure_unicode(uri))
        response = self._execute_request(self.session.delete,
                                         url,
                                         proxies=self.proxies,
                                         cookies=self.cookies,
                                         headers=self.make_headers(co3_context_token),
                                         verify=self.verify,
                                         timeout=timeout)
        if response.status_code == 204:
            # 204 - No content is OK for a delete
            return None
        BasicHTTPException.raise_if_error(response)
        return json.loads(response.text)
