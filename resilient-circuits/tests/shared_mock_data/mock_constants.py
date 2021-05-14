#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common constants used in tests"""

MOCK_PACKAGE_NAME = u"mock_function_package"

MOCK_APP_FUNCTION_PREFIX = "app_function_mock"
MOCK_APP_FN_NAME_ONE = u"{0}_{1}".format(MOCK_APP_FUNCTION_PREFIX, "one")
MOCK_APP_FN_NAME_EX = u"{0}_{1}".format(MOCK_APP_FUNCTION_PREFIX, "raise_exception")

RESILIENT_MOCK = u"pytest_resilient_circuits.BasicResilientMock"

CONFIG_DATA = """[{0}]
url = https://www.example.com""".format(MOCK_PACKAGE_NAME)


MOCK_REQUIRED_APP_CONFIGS = [
    {"name": "url", "placeholder": "https://www.example.com"}
]

MOCK_APP_CONFIGS = {
    "url": "https://www.mockexample.com"
}


MOCK_OPTS = {
    "host": "192.168.0.1",
    "org": "Test Organization",
    "email": "admin@example.com",
    "password": "123",
    "resilient_mock": RESILIENT_MOCK,
    MOCK_PACKAGE_NAME: MOCK_APP_CONFIGS
}
