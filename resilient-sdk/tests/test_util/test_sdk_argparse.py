#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import pytest
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_argparse import SDKArgumentParser


def test_sdk_argument_parser_error():

    mock_err_msg = "mock error message"
    parser = SDKArgumentParser()

    with pytest.raises(SDKException, match=r"ERROR: {0}".format(mock_err_msg)):
        parser.error(mock_err_msg)
