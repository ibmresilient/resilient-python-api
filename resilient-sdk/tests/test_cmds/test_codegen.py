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
    old_params = {
        "actions": ["rule 1", "rule 2"],
        "scripts": ["script 1"],
        "functions": []
    }

    class args(object):
        function = ["new_fn_1", "new_fn_2"]
        rule = ["rule 3"]
        script = None

    mapping_tuples = [
        ("function", "functions"),
        ("rule", "actions"),
        ("script", "scripts")
    ]

    merged_args = CmdCodegen.merge_codegen_params(old_params, args, mapping_tuples)

    assert len(merged_args.function) == 2
    assert "new_fn_1" in merged_args.function
    assert "new_fn_2" in merged_args.function
    assert "rule 3" in merged_args.rule
    assert "script 1" in merged_args.script


def test_gen_function():
    # TODO:
    pass


def test_gen_package():
    # TODO:
    pass


def test_reload_package():
    # TODO:
    pass