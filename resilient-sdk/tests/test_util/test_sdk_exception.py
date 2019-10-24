#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import pytest
from resilient_sdk.util.sdk_exception import SDKException


def mock_raise_sdk_exception(cmd, msg):
    SDKException.command_ran = cmd
    raise SDKException(msg)


def test_sdk_exception():

    mock_cmd_name = "mock_cmd"
    mock_err_msg = "A Mock Error Message"

    with pytest.raises(SDKException, match=r"resilient-sdk {0} FAILED\nERROR: {1}".format(mock_cmd_name, mock_err_msg)):
        mock_raise_sdk_exception(mock_cmd_name, mock_err_msg)
