#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common paths used in tests"""

import os

SHARED_MOCK_DATA_DIR = os.path.dirname(os.path.realpath(__file__))
TESTS_DIR = os.path.dirname(SHARED_MOCK_DATA_DIR)

TEST_TEMP_DIR = os.path.join(TESTS_DIR, "test_temp")

MOCK_RESPONSES_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_responses")
MOCK_SECRETS_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_secrets")
MOCK_PLUGINS_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_plugins")

