#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging
from datetime import datetime, timedelta

import requests
from cachetools import TTLCache, cached
from resilient_app_config_plugins import constants
from resilient_app_config_plugins.plugin_base import PAMPluginInterface, get_verify_from_string

LOG = logging.getLogger(__name__)

class IBMVerifyVault(PAMPluginInterface):
    pass # TODO
