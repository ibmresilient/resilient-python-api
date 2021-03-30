#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""Common constants used in tests"""

from resilient_circuits import helpers, constants

MOCK_ORG = "201"
MOCK_QUEUE_NAME = "mock_queue"
MOCK_SUBSCRIPTION = "{0}.{1}.{2}".format(constants.INBOUND_MSG_DEST_PREFIX, MOCK_ORG, MOCK_QUEUE_NAME)
MOCK_DESTINATION = "/queue/{0}".format(MOCK_SUBSCRIPTION)
MOCK_QUEUE = helpers.get_queue(MOCK_DESTINATION)

MOCK_PACKAGE_NAME = u"mock_function_package"
MOCK_INBOUND_Q_NAME = u"mock_inbound_q_name"
MOCK_INBOUND_Q_NAME_CREATE = u"{0}_{1}".format(MOCK_INBOUND_Q_NAME, "create")
MOCK_INBOUND_Q_NAME_EX = u"{0}_{1}".format(MOCK_INBOUND_Q_NAME, "raise_exception")

RESILIENT_MOCK = u"pytest_resilient_circuits.BasicResilientMock"

CONFIG_DATA = """[{0}]
url = https://www.example.com""".format(MOCK_PACKAGE_NAME)

MOCK_OPTS = {
    "host": "192.168.0.1",
    "org": "Test Organization",
    "email": "admin@example.com",
    "password": "123",
    "resilient_mock": RESILIENT_MOCK
}
