#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import os
import pkg_resources

PACKAGE_NAME = "resilient"

ENV_HTTP_PROXY = "HTTP_PROXY"
ENV_HTTPS_PROXY = "HTTPS_PROXY"
ENV_NO_PROXY = "NO_PROXY"

PROTECTED_SECRET_PREFIX = "$"
PROTECTED_SECRET_PREFIX_WITH_BRACKET = "${"
ALLOW_UNRECOGNIZED = False
MIN_SUPPORTED_PY3_VERSION = (3, 6)

# ENV Vars
ENV_VAR_APP_HOST_CONTAINER = "APP_HOST_CONTAINER"

# Headers
HEADER_MODULE_VER_KEY = "Resilient-Module-Version"
HEADER_MODULE_VER_VALUE = pkg_resources.get_distribution(PACKAGE_NAME).version

# Error Codes
ERROR_CODE_CONNECTION_UNAUTHORIZED = 21

# Error Messages
ERROR_MSG_CONNECTION_UNAUTHORIZED = u"Unauthorized"
ERROR_MSG_CONNECTION_INVALID_CREDS = u"Either the API Key has been blocked, the API Credentials are incorrect or the IP address has been banned. Please review the SOAR logs for more information"
WARNING_PROTECTED_SECRETS_NOT_SUPPORTED = u"Protected secrets are only supported for Python >= 3."
WARNING_DEPRECATE_EMAIL_PASS = u"Authenticating to SOAR with email and password will soon be deprecated and may be removed in a future version. Please migrate to using SOAR API Keys as soon as possible."

# File Paths
PATH_SECRETS_DIR = os.path.join(os.path.abspath(os.sep), "etc", "secrets")
PATH_JWK_FILE = os.path.join(PATH_SECRETS_DIR, ".jwk", "key.jwk")

# app configs keys
APP_CONFIG_MAX_CONNECTION_RETRIES = "max_connection_retries"
APP_CONFIG_REQUEST_MAX_RETRIES = "request_max_retries"
APP_CONFIG_REQUEST_RETRY_DELAY = "request_retry_delay"
APP_CONFIG_REQUEST_RETRY_BACKOFF = "request_retry_backoff"

# app config default values
APP_CONFIG_MAX_CONNECTION_RETRIES_DEFAULT = -1
APP_CONFIG_REQUEST_MAX_RETRIES_DEFAULT = 5
APP_CONFIG_REQUEST_RETRY_DELAY_DEFAULT = 2
APP_CONFIG_REQUEST_RETRY_BACKOFF_DEFAULT = 2

# PAM plugin constants
PAM_TYPE_CONFIG = "pam_type"
PAM_TYPE_CONFIG_APP_HOST_SECRET_NAME = "$PAM_TYPE"
PAM_DEFAULT_PAM_TYPE = "Keyring"
