#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2023. All Rights Reserved.

import logging

from six import string_types

LOG = logging.getLogger(__name__)

class PAMPluginInterface():
    """
    Base abstract class to outline required methods to be implemented by
    all app config plugins.
    """

    PAM_VERIFY_SERVER_CERT = "PAM_VERIFY_SERVER_CERT"
    PAM_ADDRESS = "PAM_ADDRESS"
    PAM_APP_ID = "PAM_APP_ID"

    def __init__(self, protected_secrets_manager, key):
        """
        Save protected_secrets_manager and "key" which indicates the level of 
        the underlying dictionary at which the plugin is positioned.

        :param protected_secrets_manager: obj for retrieving protected secrets, mostly for PAM credentials
        :type protected_secrets_manager: resilient.app_config.ProtectedSecretsManager
        :param key: dict key indicating the level at which this position is situated
        :type key: str
        """
        raise NotImplementedError("Cannot instantiate object of type {0}".format(type(self)))

    def get(self, plain_text_value, default=None):
        """
        Get value from external provider.

        ``plain_text_value`` is the value from the app.config file. As an example,
        if the config had:

            [fn_my_app]
            password=^PASS.WORD

        and ``self.options.get("password")`` is run, ``plain_text_value`` here
        will be "^PASS.WORD".

        That value should be parsed to something useable by your PAM solution's API.

        NOTE: the "^" has to be stripped out before you can use it. The recommended way to
        do that is to use ``plain_text_value.lstrip(constants.PAM_SECRET_PREFIX)``

        Any required secrets for authentication should be retrieved here using
        the protected_secrets_manager saved in the constructor.

        :param plain_text_value: plain text value from app.config (starts with "^")
        :type plain_text_value: str
        :param default: value to return if item is not found in PAM
        :type default: str
        """
        raise NotImplementedError("Implementation for PAM Interface 'get()' method is required")

    def selftest(self):
        """
        Test the configuration of the PAM plugin. This should do two things:

        1. Ensure all necessary properties are set in protected secrets
        2. Ensure that you can authenticate to the endpoint. Usually this means running
           some sort of "log in" API call

        Return True/Flase (True for successful test) and a reason as the return value.
        If anything fails, provide as useful information as you can in the second value of the tuple.

        :return: Should return (True|False, reason) where True if success and False is failure with reason for failure
        :rtype: tuple(bool, str)
        """
        raise NotImplementedError("Implementation for PAM Interface 'selftest()' method is required")

def get_verify_from_string(str_val):
    """
    Read value of 'verify' from app.config to usable
    value of True, False, or <path_to_cert_file>

    :param str_val: value in app.config
    :type str_val: str
    :return: value readable by ``requests.request(..., verify=<>)``
    :rtype: bool|str
    """
    if str_val is None or not isinstance(str_val, string_types):
        return True

    if str_val.lower() == "false":
        return False
    if str_val.lower() == "true":
        return True
    return str_val
