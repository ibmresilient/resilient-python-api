#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common Helper Functions for the resilient library"""

import logging
import os
import sys
from resilient import constants

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    from urllib import unquote
    from urlparse import urlparse
else:
    # Handle PY 3 specific imports
    from urllib.parse import urlparse, unquote

LOG = logging.getLogger(__name__)


def is_env_proxies_set():
    """
    :return: True/False if HTTP_PROXY or HTTPS_PROXY has a value
    :rtype: bool
    """
    if os.getenv(constants.ENV_HTTPS_PROXY) or os.getenv(constants.ENV_HTTP_PROXY):
        return True

    return False


def unquote_str(s):
    """
    Returns a string with the %xx replaced with their single-character
    equivalent

    If `s` None or an empty str, will just return an empty str

    :param s: String you want to unquote
    :type s: str

    :return: `s` with all %xx character replaced
    :rtype: str
    """
    if not s:
        return ""

    return unquote(s)
