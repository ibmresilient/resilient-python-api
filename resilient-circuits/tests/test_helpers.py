#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from resilient_circuits import helpers


def test_get_fn_name():

    assert helpers.get_fn_name(["don't return", "_fn_mock_integration_function"]) == "fn_mock_integration"
    assert helpers.get_fn_name(["don't return", "_fn_mock_integration_functionX"]) is None
    assert helpers.get_fn_name(["don't return", "X_fn_mock_integration_function"]) is None
