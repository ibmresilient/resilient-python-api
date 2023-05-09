#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2023. All Rights Reserved.

PAM_SECRET_PREFIX = "^"
PAM_SECRET_PREFIX_WITH_BRACKET = "^{"
DEFAULT_TIMEOUT = 30

# Cache settings for built-in plugins
CACHE_SIZE = 25
CACHE_TTL = 5 # only 5 seconds to live as credentials might rotate often
