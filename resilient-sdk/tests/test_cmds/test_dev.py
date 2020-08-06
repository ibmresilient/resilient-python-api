#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import pytest
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.cmds import base_cmd, CmdDev


def test_cmd_dev(fx_get_sub_parser, fx_cmd_line_args_dev_set_version):
    cmd_dev = CmdDev(fx_get_sub_parser)

    assert isinstance(cmd_dev, base_cmd.BaseCmd)
    assert cmd_dev.CMD_NAME == "dev"
    assert cmd_dev.CMD_HELP == "Commands used to help develop an app"
    assert cmd_dev.CMD_USAGE == """
    $ resilient-sdk dev --set-version 36.0.0"""
    assert cmd_dev.CMD_DESCRIPTION == "Commands used to help develop an app"

    args = cmd_dev.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_set_version_bad_version(fx_get_sub_parser, fx_cmd_line_args_dev_set_bad_version):
    cmd_dev = CmdDev(fx_get_sub_parser)
    args = cmd_dev.parser.parse_known_args()[0]

    with pytest.raises(SDKException, match=r"is not a valid version"):
        CmdDev._set_version(args)

