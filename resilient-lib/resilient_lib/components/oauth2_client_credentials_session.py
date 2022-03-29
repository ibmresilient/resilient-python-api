# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.
import time
import logging
import requests

log = logging.getLogger(__name__)


class OAuth2ClientCredentialsSession(requests.Session):
    """
    Wrapper around `requests.Session <https://docs.python-requests.org/en/latest/api/#requests.Session>`_
    which receives authentication tokens through the ``client_credentials`` type of OAuth2 grant,
    and adds tokens to the requests made through the session.
    It also attempts to keep track of the token and refresh it as needed.

    * If proxies are defined, every request will use them.

    This session does not request authorization from the user first. The scope should be pre-authorized.

    **Example:**

    .. code-block:: python

        from resilient_lib import OAuth2ClientCredentialsSession, RequestsCommon

        api1 = OAuth2ClientCredentialsSession('https://example1.com/<tenant_id>/oauth/v2/', client_id='xxx', client_secret='xxx')
        api2 = OAuth2ClientCredentialsSession('https://example2.com/<tenant_id>/oauth/v2/', client_id='xxx', client_secret='xxx')

        api1.post('https://example1.com/v4/me/messages', data={}) # use as a regular requests session object

        api2.get('https://example2.com/v2/me/updates')

        # When writing an integration, use RequestsCommon to get the proxies defined in in your app.config file.
        rc = RequestsCommon(opts, function_opts)
        api3 = OAuth2ClientCredentialsSession('https://example3.com/{}/test', proxies=rc.get_proxies())

    :param url: Authorization URL, with tenant_id in it, if required
    :type url: str
    :param client_id: API key/User ID
    :type client_id: str
    :param client_secret: secret for API key
    :type client_secret: str
    :param scope: (optional) list of scopes
    :type scope: [str]
    :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
            The mapping protocol must be in the format:

            .. code-block::

                {
                    "https_proxy": "https://localhost:8080,
                    "http_proxy": "http://localhost:8080
                }
    :type proxies: dict
    """

    AUTHORIZATION_ERROR_CODES = [401, 403]

    def __init__(self, url=None, client_id=None, client_secret=None, scope=None, proxies=None):
        """
        Get OAuth2 tokens and save them to be used in session requests.
        """
        # __init__ is run even if __new__ returned existing instance
        if getattr(self, "authorization_url", None) is not None:
            return

        super(OAuth2ClientCredentialsSession, self).__init__()
        log.debug("Creating OAuth2 Session.")
        if not url or not client_id or not client_secret:
            missing_fields = list()
            if not url:
                missing_fields.append("url")
            if not client_id:
                missing_fields.append("client_id")
            if not client_secret:
                missing_fields.append("client_secret")
            raise ValueError("Missing fields ({}) required for OAuth2 authentication."
                             .format(",".join(missing_fields)))

        self.authorization_url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

        self.oauth_token_data = None
        self.expires_in = None
        self.access_token = None
        self.token_type = None
        self.expiration_time = None
        self.proxies = proxies if proxies is not None else {}

        self.authenticate(url, client_id, client_secret, scope, proxies)

    def authenticate(self, url, client_id, client_secret, scope, proxies=None):
        """
        Authenticate with the endpoint
        """
        token_url = url

        log.debug("Requesting token from {0}".format(url))
        r = self.get_token(token_url, client_id, client_secret, scope, proxies)

        log.info("Response status code: {}".format(r.status_code))
        r.raise_for_status()

        self.oauth_token_data = r.json()
        log.debug("Received oauth token.")

        self.expires_in = self.oauth_token_data.get("expires_in", None)
        if self.expires_in is not None:
            self.expiration_time = time.time() + int(self.expires_in)
        else:
            self.expiration_time = None

        self.access_token = self.oauth_token_data["access_token"]
        self.token_type = self.oauth_token_data.get("token_type", None)

        return True

    def get_token(self, token_url, client_id, client_secret, scope=None, proxies=None):
        """
        **Override this method if the request needs specific information in the
        body of the request**

        For example, *Cloud Foundry* asking ``grant_type`` to be ``password`` and API key to be passed in ``password``.

        The default is:

        .. code-block:: python

            post_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials'
            }

            if scope:
                post_data['scope'] = scope

        :param token_url: Authorization URL, with tenant_id in it, if required
        :type token_url: str
        :param client_id: API key/User ID
        :type client_id: str
        :param client_secret: secret for API key
        :type client_secret: str
        :param scope: (optional) list of scopes
        :type scope: [str]
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :type proxies: dict
        :return: the ``response`` from the ``token_url``
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_
        """
        post_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        if scope:
            post_data['scope'] = scope
        return self.post(token_url, data=post_data, proxies=proxies)

    def update_token(self):
        """
        Institutes a request for a new access token.

        :raises ValueError: If it cannot update the token
        :return: True if could get a new token
        :rtype: bool
        """
        try:
            self.authenticate(self.authorization_url, self.client_id,
                              self.client_secret, self.scope, self.proxies)
        except ValueError:
            raise ValueError("Can't update the token, did the credentials for {0} change?"
                             .format(self.authorization_url))
        return True

    def request(self, method, url, *args, **kwargs):
        """Constructs a `requests.Request <https://docs.python-requests.org/en/latest/api/#requests.Request>`_,
        injects it with tokens and sends it in a new session to avoid having one session constantly open.

        This uses the ``requests.request()`` function to
        make a call. The inputs are mapped to this function.
        See `requests.request() <https://docs.python-requests.org/en/latest/api/#requests.request>`_
        for information on any parameters available

        :return: the ``response`` object
        :rtype: `requests.Response <https://docs.python-requests.org/en/latest/api/#requests.Response>`_
        """

        # Don't check expiration if attempting to refresh authorization - would cause infinite recursion loop
        if self.expiration_time is not None and url != self.authorization_url:
            if self.expiration_time < time.time():
                self.update_token()

        headers = kwargs.pop("headers") if "headers" in kwargs else {}
        proxies = kwargs.pop("proxies") if "proxies" in kwargs else self.proxies
        self.add_authorization_header(headers)

        resp = super(OAuth2ClientCredentialsSession, self).request(method, url, *args, headers=headers, proxies=proxies,
                                                                   **kwargs)

        # If the error anything other than Authorization issue, the problem is in user's request
        if resp.status_code in self.AUTHORIZATION_ERROR_CODES:
            self.update_token()
            resp = super(OAuth2ClientCredentialsSession, self).request(method, url, *args, headers=headers,
                                                                        proxies=proxies, **kwargs)

        return resp

    def add_authorization_header(self, headers):
        """
        Create headers needed for authentication/authorization, overriding the default ones if needed.

        :param headers: Dictionary containing the ``Authorization`` header
        :type headers: dict
        """
        headers["Authorization"] = "{} {}".format(self.token_type, self.access_token)
