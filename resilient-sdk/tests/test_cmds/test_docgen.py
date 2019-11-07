#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import sys
from resilient_sdk.cmds import base_cmd, CmdDocgen


def test_cmd_docgen_setup(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)

    assert isinstance(cmd_docgen, base_cmd.BaseCmd)
    assert cmd_docgen.CMD_NAME == "docgen"
    assert cmd_docgen.CMD_HELP == "Generate documentation for an Extension"
    assert cmd_docgen.CMD_USAGE == """
    $ resilient-sdk docgen -p <path_to_package>
    $ resilient-sdk docgen -p <path_to_package> --only-user-guide
    $ resilient-sdk docgen -p <path_to_package> --only-install-guide"""
    assert cmd_docgen.CMD_DESCRIPTION == "Generate documentation for an Extension"

    args = cmd_docgen.parser.parse_known_args()[0]
    assert args.p == "fn_main_mock_integration"
    assert args.only_install_guide is False
    assert args.only_user_guide is False


def test_only_install_guide_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--only-install-guide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.only_install_guide is True
    assert args.only_user_guide is False


def test_only_install_user_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--only-user-guide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.only_install_guide is False
    assert args.only_user_guide is True


def test_get_fn_input_details():
    # TODO: taken from old docgen
    pass


def test_get_function_details():
    # TODO: taken from old docgen
    pass


def test_get_rule_details():
    # TODO: taken from old docgen
    pass


def test_get_datatable_details():
    # TODO: taken from old docgen
    pass


def test_get_custom_fields_details():
    # TODO: taken from old docgen
    pass


def test_get_custom_artifact_details():
    # TODO: taken from old docgen
    pass


def test_execute_command():
    # TODO
    pass