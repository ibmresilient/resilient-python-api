#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2023. All Rights Reserved.

import logging
from datetime import datetime, timedelta

import requests
from cachetools import TTLCache, cached
from resilient_app_config_plugins import constants
from resilient_app_config_plugins.plugin_base import (PAMPluginInterface,
                                                      get_verify_from_string)
from six.moves.urllib.parse import urljoin

LOG = logging.getLogger(__name__)

class HashiCorpVault(PAMPluginInterface):
    """
    App Config plugin to connect to HashiCorp Vault's KV (key-value) secrets engine

    This class can be subclassed and used to implement custom plugins
    for other HashiCorp Vault secret engines. Each would need to overwrite
    the ``get()`` method and implement the REST call required for that engine.
    See details on HashiCorp's APIs here: https://developer.hashicorp.com/vault/api-docs/secret
    The ``_get_access_token()`` method will work fine as long as proper policies
    are set for the app role to access the secrets in any given engine.
    """
    SECRET_ID = "PAM_SECRET_ID"
    REQUIRED_CONFIGS = [PAMPluginInterface.PAM_ADDRESS, PAMPluginInterface.PAM_APP_ID, SECRET_ID]

    VAULT_API_VERSION = "v1"
    VAULT_LOGON_URI = "{0}/auth/approle/login".format(VAULT_API_VERSION)
    VAULT_KV_DATA_URI = "{0}/{1}/data/{2}"

    def __init__(self, protected_secrets_manager, key, *args, **kwargs):
        self.protected_secrets_manager = protected_secrets_manager
        self.key = key # unused in hashicorp, but relevant to others -- here for demo puposes

        self.client_token = None
        self.lease_expiration = datetime.utcnow()

    def _get_access_token(self):
        """
        Either on first try or on token expiration,
        reach out to HashiCorp to get client token using
        role_id and secret_id provided in protected secrets.
        """
        time_before_request = datetime.utcnow()


        # check if any configs are missing from the required list
        # NOTE: this will only be called when a item is needed
        # and the token doesn't yet exist or is expired. If the configurations
        # required to get the client token are incorrect, but a item is
        # never requested from HashiCorp, then no error will be raised.
        missing = [key for key in self.REQUIRED_CONFIGS if not self.protected_secrets_manager.get(key)]
        if any(missing):
            raise ValueError("Missing one (or more) required configuration(s): {0} for adapter type '{1}'".format(missing, self.__class__.__name__))

        # assuming all required configs are present from here on out:
        # gather role_id, secret_id, and vault_address from protected secrets
        role_id = self.protected_secrets_manager.get(self.PAM_APP_ID)
        secret_id = self.protected_secrets_manager.get(self.SECRET_ID)
        vault_address = self.protected_secrets_manager.get(self.PAM_ADDRESS)
        verify = get_verify_from_string(self.protected_secrets_manager.get(self.PAM_VERIFY_SERVER_CERT))

        # call to login endpoint
        # NOTE: no try-except here; any requests exceptions that are
        # raised should be allowed to go through and fail circuits.
        # The only error handling that takes place is in the search for
        # "errors" in the response, which are server-side and can be handled as
        # needed
        try:
            response = requests.post(
                urljoin(vault_address, self.VAULT_LOGON_URI),
                data={
                    "role_id": role_id,
                    "secret_id": secret_id
                },
                timeout=constants.DEFAULT_TIMEOUT,
                verify=verify
            ).json()

            # there may be errors returned from the endpoint
            # those are fatal in this case as the client token
            # is required to run the app, but the endpoint was not
            # able to provide the token thus we need to stop circuits
            if "errors" in response:
                raise ValueError("Unable to login to HashiCorp approle endpoint. Error(s): {0}".format(response.get("errors")))

            # if no errors, capture client token and lease duration information
            # NOTE: lease duration is harder to parse in a useful way so we
            # calculate the expiration time given the duration information
            self.client_token = response.get("auth").get("client_token")
            self.lease_expiration = time_before_request + timedelta(0, response.get("auth").get("lease_duration"))
        except requests.exceptions.SSLError as e:
            LOG.error("Unable to verify connection to HashiCorp. PAM connection will not be able to be used. If you have a self-signed cert for you HashiCorp server, set {0}=false".format(self.PAM_VERIFY_SERVER_CERT))
        except Exception as e:
            LOG.error("Unable to login to HashiCorp Vault. Error: {0}".format(str(e)))

    def _get_pv_vault_data(self, secrets_engine, path):
        """
        Send request to secrets engine for given path to get
        key-value details.

        The returned value should contain a data.data.<credential_name>
        value which holds the secret.

        :param secrets_engine: name of the secrets engine (e.g. 'secret')
        :type secrets_engine: str
        :param path: path to secret in vault (e.g. 'my/path')
        :type path: str
        :return: secret value from KV secret engine
        :rtype: str
        """
        vault_address = self.protected_secrets_manager.get(self.PAM_ADDRESS)
        verify = get_verify_from_string(self.protected_secrets_manager.get(self.PAM_VERIFY_SERVER_CERT))
        response = requests.get(
            urljoin(
                vault_address,
                self.VAULT_KV_DATA_URI.format(self.VAULT_API_VERSION, secrets_engine, path)
            ),
            headers={
                "X-Vault-Token": self.client_token
            },
            timeout=constants.DEFAULT_TIMEOUT,
            verify=verify
        ).json()

        if "errors" in response:
            raise ValueError("Unable to get value for '{0}' from HashiCorp Vault. Error(s): {1}".format(path, response.get("errors")))
        
        return response

    # each item is cached, but only 5 seconds to live as values could be rotated relatively quickly
    # the caching helps on startup if many values are required quickly in succession
    @cached(cache=TTLCache(maxsize=constants.CACHE_SIZE, ttl=constants.CACHE_TTL))
    def get(self, plain_text_value, default=None):
        """
        Get item from KV engine. NOTE: only works with KV (key-value) engine

        If not authenticated yet, or authentication expired, first call
        ``self._get_access_token()`` to refresh access token.

        Plain text value requires very specific formatting. Separated by ".", 
        the following three items must be provided:

            1. secrets engine name in Vault
            2. path to secret within engine
            3. name of specific key to get the value for

        **Example:**

        If my engine is called ``secret``, the path is ``mysql/webapp`` and the credential
        I want to retrieve has a key ``password``, then I can use the following syntax
        for for ``plain_text_value``: ``^secret.mysql/webapp.password``.
        Or, in my app.config for some app ``fn_my_app``, I can set ``password`` to be
        resolved from Vault like so:

        .. code-block::

            [fn_my_app]
            password=^secret.mysql/webapp.password

        :param plain_text_value: plain text vaule found in app.config (like ^<engine>.m<path>.<key>)
        :type plain_text_value: str
        :param default: value to return if item is not found in PAM; defaults to None
        :type default: str
        :return: value for key found in Vault
        :rtype: str
        """
        item = plain_text_value.lstrip(constants.PAM_SECRET_PREFIX)
        split = item.split(".")

        if len(split) == 3:
            secrets_engine = split[0]
            path = split[1]
            credential_name = split[2]
        else:
            LOG.error("HashiCorpVault value '%s' was not properly formatted. Please review the formatting guide for this plugin in the documentation", plain_text_value)
            return default

        if not self.client_token or datetime.utcnow() >= self.lease_expiration:
            self._get_access_token()

        if not self.client_token:
            return default

        try:
            response = self._get_pv_vault_data(secrets_engine, path)

            # it is possible that some secrets are "deleted" or "destroyed" in the secrets
            # vault. handle these situations and alert the retriever of the issue
            if not response.get("data") or not response.get("data", {}).get("data"):
                cred_version = response.get("data", {}).get("metadata", {}).get("version")
                if response.get("data", {}).get("metadata", {}).get("destroyed") == True:
                    # "destroyed" but not "deleted" case
                    raise ValueError("Latest version (v{0}) of '{1}' was destroyed in vault. Please update a new version to use this secret".format(cred_version, path))
                else:
                    # "deleted" case
                    raise ValueError("No data found for version v{0} HashiCorp secret at '{1}'".format(cred_version, path))

            return response["data"]["data"][credential_name]
        except KeyError as err:
            LOG.error("Error retrieving {0} from HashiCorpVault. Details: {1}".format(plain_text_value, str(err)))
            return default

    def selftest(self):
        """
        Check if the endpoint is live by running ``_get_access_token()``
        which will first check that each required value is present,
        and then "log in" to the endpoint with the role id and secret.

        If anything goes wrong, ``_get_access_token()`` raises a ValueError.
        Capture the error and return that as the reason for the failed
        selftest.

        :return: True if all required values are present and can authenticate, False otherwise
        :rtype: tuple(bool, str)
        """
        try:
            self._get_access_token()
            if not self.client_token:
                return False, "Couldn't authenticate to HashiCorp Vault"
        except ValueError as err:
            return False, str(err)
        except requests.exceptions.RequestException as err:
            return False, str(err)

        return True, ""
