#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from resilient_sdk.cmds import base_cmd, CmdExtract


def test_cmd_extract_setup(fx_get_sub_parser, fx_cmd_line_args_extract):
    cmd_extract = CmdExtract(fx_get_sub_parser)

    assert isinstance(cmd_extract, base_cmd.BaseCmd)

    assert cmd_extract.CMD_NAME == "extract"
    assert cmd_extract.CMD_HELP == "Extracts data needed to publish a .res file."
    assert cmd_extract.CMD_USAGE == """
    $ resilient-sdk extract -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
    $ resilient-sdk extract --playbook my_sub_playbook --function fn_in_sub_playbook
    $ resilient-sdk extract --script 'custom_script' --zip
    $ resilient-sdk extract --script 'custom_script' --zip -c '/usr/custom_app.config'
    $ resilient-sdk extract --script 'custom_script' --name 'my_custom_export'"""
    assert cmd_extract.CMD_DESCRIPTION == "Extract data in order to publish a .res export file"
    assert cmd_extract.CMD_ADD_PARSERS == ["app_config_parser", "res_obj_parser", "io_parser", "zip_parser"]


def test_execute_command():
    # TODO
    pass