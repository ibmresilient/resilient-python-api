#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common paths used in tests"""

import os

SHARED_MOCK_DATA_DIR = os.path.dirname(os.path.realpath(__file__))

MOCK_APP_CONFIG = os.path.join(SHARED_MOCK_DATA_DIR, "mock_app_config")
MOCK_COMMENTED_APP_CONFIG = os.path.join(SHARED_MOCK_DATA_DIR, "mock_commented_app_config")
MOCK_COMPONENT = os.path.join(SHARED_MOCK_DATA_DIR, "mock_component.py")
MOCK_IMPORT_DEFINITION = os.path.join(SHARED_MOCK_DATA_DIR, "mock_import_definition.txt")