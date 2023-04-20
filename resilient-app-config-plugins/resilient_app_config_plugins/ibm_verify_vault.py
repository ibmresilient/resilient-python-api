#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging
from datetime import datetime, timedelta

import requests
from cachetools import TTLCache, cached
from resilient_app_config_plugins import HashiCorpVault, constants
from resilient_app_config_plugins.plugin_base import (PAMPluginInterface,
                                                      get_verify_from_string)
from six.moves.urllib.parse import urljoin

LOG = logging.getLogger(__name__)

class IBMVerifyVault(PAMPluginInterface):

    VAULT_TOKEN = "VAULT_TOKEN"
    REQUIRED_CONFIGS = [PAMPluginInterface.PAM_ADDRESS, VAULT_TOKEN]

    VAULT_API_VERSION_SUFFIX = "/api/v1"

    def __init__(self, protected_secrets_manager, *args, **kwargs):
        self.protected_secrets_manager = protected_secrets_manager

    def get(self, plain_text_value, default=None):
        vault_address = self.protected_secrets_manager.get(self.PAM_ADDRESS)
        vault_address = urljoin(vault_address, self.VAULT_API_VERSION_SUFFIX)
        token = self.protected_secrets_manager.get(self.VAULT_TOKEN)
        verify = get_verify_from_string(self.protected_secrets_manager.get(self.PAM_VERIFY_SERVER_CERT))

        split = plain_text_value.split(".")

        if len(split) == 2:
            secret_id = split[0]
            slug = split[1]
        else:
            LOG.error("TODO")
            return default

        headers = {
            "Authorization": "Bearer {0}".format(token),
            "content-type": "application/json"
        }

        resp = requests.get(
            urljoin(vault_address, "/secrets/{0}".format(secret_id)),
            headers=headers,
            timeout=constants.DEFAULT_TIMEOUT,
            verify=verify
        )

        if resp.status_code not in (200, 304):
            raise ValueError("Error retrieving Secret. %s %s" % (resp.status_code, resp))
        
        items = resp.json().get("items", [])

        for item in items:
            if item.get("slug") == slug:
                return item.get("itemValue")
        raise ValueError("TODO")
