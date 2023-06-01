#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2023. All Rights Reserved.

import base64
import logging

import requests_pkcs12 as requests  # required as this allows for .p12 cert files
from cachetools import TTLCache, cached
from requests.exceptions import RequestException, SSLError
from resilient_app_config_plugins import constants
from resilient_app_config_plugins.plugin_base import (PAMPluginInterface,
                                                      get_verify_from_string)
from six.moves.urllib.parse import urljoin

LOG = logging.getLogger(__name__)

class Cyberark(PAMPluginInterface):
    """
    App Config plugin to connect to Cyberark's Central Credential Provider
    """
    CERT_PATH = "PAM_CERT_PATH"
    CERT_PASS_KEY = "PAM_CERT_PASSWORD"
    REQUIRED_CONFIGS = [PAMPluginInterface.PAM_ADDRESS, PAMPluginInterface.PAM_APP_ID, CERT_PATH, CERT_PASS_KEY]


    CYBERARK_BASE_ACCOUNT_URI = "/AIMWebService/api/Accounts"
    CYBERARK_ACCOUNTS_URI = CYBERARK_BASE_ACCOUNT_URI + "?appid={0}&safe={1}&object={2}"

    def __init__(self, protected_secrets_manager, key):
        self.protected_secrets_manager = protected_secrets_manager
        self.key = key

    def _check_required_params_present(self):
        """
        Checks that all required configs are present in the env as protected secrets.

        :raises ValueError: If any configs are missing
        """
        missing = [key for key in self.REQUIRED_CONFIGS if not self.protected_secrets_manager.get(key)]
        if any(missing):
            raise ValueError("Missing one (or more) required configuration(s): {0} for adapter type '{1}'".format(missing, self.__class__.__name__))

    def _get_cert_details(self):
        """
        Read certificate stream and password to unlock.
        
        Public cert and private key combined into one file,
        must be base64 encoded version of the PKCS12 password
        protected version of the cert-key combo file.

        :return: base64 decoded byte stream of the cert/key file, password to decrypt
        :rtype: tuple(bytes, str)
        """
        password = self.protected_secrets_manager.get(self.CERT_PASS_KEY)

        file_path = self.protected_secrets_manager.get(self.CERT_PATH)
        with open(file_path, "r", encoding="utf-8") as encoded:
            base64_stream = base64.b64decode(encoded.read())

        return base64_stream, password
    
    def _get_account_details(self, safe, obj):
        """
        Make a request to the Central Credential Provider via the REST API
        and return the result. Results from this endpoint contain the password
        and some metadata. The resulting object from this function is the
        ``requests.Response`` object and the .json() values from that object are
        useful in the case of a successful request.

        **Example** response with ``appid=testappid&safe=Test&object=Website-GenericWebApp-example.com-webapp``:

        .. code-block::json

            {'Content': 'PASSWORD_HERE',
            'PolicyID': 'GenericWebApp',
            'CreationMethod': 'PVWA',
            'Folder': 'Root',
            'Address': 'example.com',
            'Name': 'Website-GenericWebApp-example.com-webapp',
            'Safe': 'Test',
            'DeviceType': 'Website',
            'UserName': 'webapp',
            'PasswordChangeInProcess': 'False'}

        :param safe: name of the safe to search
        :type safe: str
        :param obj: name of the object to search for in the safe
        :type obj: str
        :raises ValueError: if missing any required configurations
        :return: response from API request
        :rtype: ``requests.Response``
        """
        self._check_required_params_present()

        base_url = self.protected_secrets_manager.get(self.PAM_ADDRESS)
        app_id = self.protected_secrets_manager.get(self.PAM_APP_ID)
        verify = get_verify_from_string(self.protected_secrets_manager.get(self.PAM_VERIFY_SERVER_CERT))

        pkcs12_stream, pkcs12_password = self._get_cert_details()

        try:
            return requests.get(
                urljoin(
                    base_url,
                    self.CYBERARK_ACCOUNTS_URI.format(app_id, safe, obj)
                ),
                pkcs12_data=pkcs12_stream,
                pkcs12_password=pkcs12_password,
                verify=verify,
                timeout=constants.DEFAULT_TIMEOUT
            )
        except SSLError:
            LOG.error("Unable to verify connection to Cyberark. PAM connection will not be able to be used. If you have a self-signed cert for you Cyberark server, set {0}=false".format(self.PAM_VERIFY_SERVER_CERT))
        except Exception as e:
            LOG.error("Unable to connect to Cyberark. Error: {0}".format(str(e)))

    @cached(cache=TTLCache(maxsize=constants.CACHE_SIZE, ttl=constants.CACHE_TTL))
    def get(self, plain_text_value, default=None):
        """
        Get value from Cyberark given "^"-prefixed key in app.config

        :param plain_text_value: "^"-prefixed value from app.config
        :type plain_text_value: str
        :param default: value to return if item is not found in PAM; defaults to None
        :type default: str
        :return: value retrieved from "Content" (password) field from CCP
        :rtype: str
        """
        item = plain_text_value.lstrip(constants.PAM_SECRET_PREFIX)

        split = item.split("/")
        
        if len(split) == 2:
            safe = split[0]
            obj = split[1]
        else:
            LOG.error("Cyberark value '%s' was not properly formatted. Please review the formatting guide for this plugin in the documentation", plain_text_value)
            return default

        response = self._get_account_details(safe, obj)

        if not response or not hasattr(response, "json"):
            return default

        return response.json().get("Content", default)

    def selftest(self):
        """
        Check if the endpoint is live by running an API request to the CCP endpoint
        and check if all required configs are given.

        :return: True if all required values are present and can authenticate, False otherwise
        :rtype: tuple(bool, str)
        """
        try:
            self._check_required_params_present()
        except ValueError as err:
            return False, str(err)

        base_url = self.protected_secrets_manager.get(self.PAM_ADDRESS)
        app_id = self.protected_secrets_manager.get(self.PAM_APP_ID)
        verify = get_verify_from_string(self.protected_secrets_manager.get(self.PAM_VERIFY_SERVER_CERT))

        pkcs12_stream, pkcs12_password = self._get_cert_details()

        try:
            response = requests.get(
                urljoin(base_url, self.CYBERARK_BASE_ACCOUNT_URI.format(app_id)),
                pkcs12_data=pkcs12_stream,
                pkcs12_password=pkcs12_password,
                verify=verify,
                timeout=constants.DEFAULT_TIMEOUT
            )
        except ValueError as err: # requests_pkcs12 raises ValueError if can't use cert/password
            return False, str(err)
        except RequestException as err:
            return False, str(err)

        if response.status_code == 403: # 400 might be raised, but that's ok -- only 403 indicates improper validation
            return False, "Could not authenticate to Cyberark with given credentials"

        return True, ""
