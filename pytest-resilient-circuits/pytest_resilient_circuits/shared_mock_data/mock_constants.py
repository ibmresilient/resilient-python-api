#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""Common constants used in tests"""


RESILIENT_MOCK = u"pytest_resilient_circuits.BasicResilientMock"

MOCK_APP_CONFIGS = {
    "host": "192.168.0.1",
    "org": "Test Organization",
    "email": "admin@example.com",
    "password": "123",
    "resilient_mock": RESILIENT_MOCK
}
