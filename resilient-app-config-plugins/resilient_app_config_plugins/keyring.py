#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging

import keyring
from cachetools import TTLCache, cached
from resilient_app_config_plugins import constants
from resilient_app_config_plugins.plugin_base import PAMPluginInterface

try:
    from keyring.errors import KeyringError
except ImportError:
    KeyringError = Exception

LOG = logging.getLogger(__name__)

class Keyring(PAMPluginInterface):
    """
    Default PAM plugin to work with Keyring.
    This works with the keyring library and the built-in OS
    backend for keyring. Integration server only;
    not compatible with AppHost.
    """

    def __init__(self, *args, **kwargs):
        self.key = kwargs.get("key", "_")

    @cached(cache=TTLCache(maxsize=constants.CACHE_SIZE, ttl=constants.CACHE_TTL))
    def get(self, plain_text_value):
        """
        Using ``keyring.get_password``, retrieve secret from keyring.

        Note that the ``"resilient"`` service is special and stored as
        ``"_"`` when set with ``res-keyring`` utility. So that is handled
        differently here.

        NOTE: keyring only works if you first set the values using ``res-keyring``

        :param plain_text_value: value in app.config like ``pass=^value``
        :type plain_text_value: str
        :return: value found in keyring
        :rtype: str
        """
        item = plain_text_value.lstrip(constants.PAM_SECRET_PREFIX)
        service = self.key
        if service == "resilient":
            # Special case, becuase of the way we parse commandlines, treat this as root
            service = "_"
        LOG.debug("keyring get('%s', '%s')", service, item)
        try:
            return keyring.get_password(service, item)
        except KeyringError as err:
            LOG.error("Keyring object was requested from app.config but no suitable backend was found. More info: {0}".format(str(err)))
            return plain_text_value

    def selftest(self):
        """
        No need to actually test anything here -- just implementing for
        parent class requirement

        :return: True, ""
        :rtype: tuple(bool, str)
        """
        return True, ""
