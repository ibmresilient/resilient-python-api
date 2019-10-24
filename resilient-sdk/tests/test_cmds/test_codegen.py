#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

from resilient_sdk.cmds import base_cmd, CmdCodegen


def test_cmd_codegen(fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)

    assert isinstance(cmd_codegen, base_cmd.BaseCmd)
    assert cmd_codegen.CMD_NAME == "codegen"
    assert cmd_codegen.CMD_HELP == "Generate boilerplate code to start developing an Extension"
    assert cmd_codegen.CMD_USAGE == "resilient-sdk codegen -p <name_of_package> -m <message_destination>"
    assert cmd_codegen.CMD_DESCRIPTION == "Generate boilerplate code to start developing an Extension"
    assert cmd_codegen.CMD_USE_COMMON_PARSER_ARGS is True

    args = cmd_codegen.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_render_jinja_mapping():
    # TODO:
    pass


def test_merge_codegen_params():
    # TODO:
    pass


def test_gen_function():
    # TODO:
    pass


def test_gen_package():
    # TODO:
    pass


def test_reload_package():
    # TODO:
    pass