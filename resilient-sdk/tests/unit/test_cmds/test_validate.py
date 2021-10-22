#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_sdk.cmds import base_cmd, CmdValidate


def test_validate_setup(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_validate):
    cmd_validate = CmdValidate(fx_get_sub_parser)

    assert isinstance(cmd_validate, base_cmd.BaseCmd)
    assert cmd_validate.CMD_NAME == "validate"
    assert cmd_validate.CMD_HELP == "Validate an App before packaging it"
    assert cmd_validate.CMD_USAGE == """
    $ resilient-sdk validate -p <name_of_package>
    $ resilient-sdk validate -p <name_of_package> --validate
    $ resilient-sdk validate -p <name_of_package> --tests
    $ resilient-sdk validate -p <name_of_package> --pylint --bandit --cve --selftest"""
    assert cmd_validate.CMD_DESCRIPTION == cmd_validate.CMD_HELP

    args = cmd_validate.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    assert bool(not args.validate and not args.tests and not args.pylint and not args.bandit and not args.cve) is True


def test_execute_command():
    # TODO
    pass