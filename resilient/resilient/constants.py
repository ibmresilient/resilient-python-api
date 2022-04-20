#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pkg_resources

PACKAGE_NAME = "resilient"

ENV_HTTP_PROXY = "HTTP_PROXY"
ENV_HTTPS_PROXY = "HTTPS_PROXY"
ENV_NO_PROXY = "NO_PROXY"

# Headers
HEADER_MODULE_VER_KEY = "Resilient-Module-Version"
HEADER_MODULE_VER_VALUE = pkg_resources.get_distribution(PACKAGE_NAME).version

ALLOW_UNRECOGNIZED = False

# Error Codes
ERROR_CODE_CONNECTION_UNAUTHORIZED = 21

# Error Messages
ERROR_MSG_CONNECTION_UNAUTHORIZED = u"Unauthorized"
ERROR_MSG_CONNECTION_INVALID_CREDS = u"Either the API Key has been blocked, the API Credentials are incorrect or the IP address has been banned. Please review the SOAR logs for more information"
