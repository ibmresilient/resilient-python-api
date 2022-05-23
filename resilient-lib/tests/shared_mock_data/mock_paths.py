#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common paths used in tests"""

import os

SHARED_MOCK_DATA_DIR = os.path.dirname(os.path.realpath(__file__))
MOCK_CERTS_DIR = os.path.join(SHARED_MOCK_DATA_DIR, "mock_certs")

MOCK_CLIENT_CERT_FILE = os.path.join(MOCK_CERTS_DIR, "cert.pem")
MOCK_CLIENT_KEY_FILE = os.path.join(MOCK_CERTS_DIR, "key.open.pem")
