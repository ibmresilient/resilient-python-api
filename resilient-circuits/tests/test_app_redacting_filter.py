#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.


import logging
import sys

import pytest
from resilient_circuits import constants
from resilient_circuits.app import RedactingFilter


@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python 3")
def test_clears_sensitive_info(caplog):
    caplog.set_level(logging.DEBUG)
    logger = logging.getLogger("test1")
    logger.addFilter(RedactingFilter())

    data = {
        "seems_good": "found",
        "secret": "will be removed"
    }

    logger.info(data)

    assert "'seems_good': 'found', 'secret': '***'" in caplog.text
    assert "will be removed" not in caplog.text

@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python 3")
def test_clears_sensitive_info_with_multiple(caplog):
    caplog.set_level(logging.DEBUG)
    logger = logging.getLogger("test2")
    logger.addFilter(RedactingFilter())

    data = {
        "seems_good": "found",
        "secret": "superdupersecret",
        "api_key": "12345abcde",
        "something_that_should_show": "found it!"
    }

    logger.info(data)

    assert "'seems_good': 'found', 'secret': '***', 'api_key': '***', 'something_that_should_show': 'found it!'" in caplog.text
    assert data.get("secret") not in caplog.text
    assert data.get("api_key") not in caplog.text

@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python 3")
def test_all_password_prefixes_removed(caplog):
    caplog.set_level(logging.DEBUG)
    logger = logging.getLogger("test3")
    logger.addFilter(RedactingFilter())

    data = {}
    for prefix in constants.PASSWORD_PATTERNS:
        data[prefix] = "{} and some text".format(prefix)

    logger.info(data)

    for prefix in constants.PASSWORD_PATTERNS:
        assert "{} and some text".format(prefix) not in caplog.text
        assert "'{}': '***'".format(prefix) in caplog.text

    assert "': '***', '".join(constants.PASSWORD_PATTERNS) in caplog.text
