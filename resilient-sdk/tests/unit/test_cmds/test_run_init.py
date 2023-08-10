#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import json
import os
import sys

import pytest
from mock import patch
from resilient_sdk.cmds import CmdRunInit, base_cmd
from resilient_sdk.util import constants
from tests.shared_mock_data import mock_paths


def test_cmd_init_setup(fx_get_sub_parser, fx_cmd_line_args_init):
    cmd_init = CmdRunInit(fx_get_sub_parser)

    assert isinstance(cmd_init, base_cmd.BaseCmd)
    assert cmd_init.CMD_NAME == "init"
    assert cmd_init.CMD_HELP == "Generates sdk_settings.json to store default settings."
    assert cmd_init.CMD_USAGE == """
    $ resilient-sdk init
    $ resilient-sdk init -f/--file <path to settings json>
    $ resilient-sdk init -f/--file <path to settings json> -a/--author you@example.com
    """
    assert cmd_init.CMD_DESCRIPTION == cmd_init.CMD_HELP

def test_file_creation(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path):
    cmd_init = CmdRunInit(fx_get_sub_parser)
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    assert os.path.exists(constants.SDK_SETTINGS_FILE_PATH)

@pytest.mark.skipif(sys.version_info.major > 2, reason="requires python 2")
def test_input_py2(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_create_mock_settings_file, caplog):
    with patch("resilient_sdk.cmds.run_init.raw_input", return_value="n"):
        cmd_init = CmdRunInit(fx_get_sub_parser)
        args = cmd_init.parser.parse_known_args()[0]
        cmd_init.execute_command(args)
        assert "Will not overwrite" in caplog.text

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_input_py3(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_create_mock_settings_file, caplog):
    with patch("resilient_sdk.cmds.run_init.input", return_value="n"):
        cmd_init = CmdRunInit(fx_get_sub_parser)
        args = cmd_init.parser.parse_known_args()[0]
        cmd_init.execute_command(args)
        assert "Will not overwrite" in caplog.text

def test_default_settings(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path):
    cmd_init = CmdRunInit(fx_get_sub_parser)
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    with open(constants.SDK_SETTINGS_FILE_PATH) as f:
        settings_json = json.load(f)
        assert settings_json.get("codegen").get("setup").get("author") == constants.CODEGEN_DEFAULT_SETUP_PY_AUTHOR
        assert settings_json.get("codegen").get("setup").get("author_email") == constants.CODEGEN_DEFAULT_SETUP_PY_EMAIL
        assert settings_json.get("codegen").get("setup").get("url") == constants.CODEGEN_DEFAULT_SETUP_PY_URL
        assert settings_json.get("codegen").get("setup").get("license") == constants.CODEGEN_DEFAULT_SETUP_PY_LICENSE
        assert "<<{}>>".format(constants.DOCGEN_PLACEHOLDER_STRING) in settings_json.get("codegen").get("setup").get("long_description")
        assert """Enter a long description, including the key features of the App. \\\nMultiple continuation lines are supported with a backslash.""" \
            in settings_json.get("codegen").get("setup").get("long_description")
        assert settings_json.get("codegen").get("license_content") == constants.CODEGEN_DEFAULT_LICENSE_CONTENT
        assert settings_json.get("codegen").get("copyright") == constants.CODEGEN_DEFAULT_COPYRIGHT_CONTENT
        assert settings_json.get("docgen").get("supported_app") == False
        

def test_custom_settings_path(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init):
    cmd_init = CmdRunInit(fx_get_sub_parser)
    my_new_path = "{}/my_test.json".format(mock_paths.TEST_TEMP_DIR)
    sys.argv.extend(["--file", my_new_path])
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    assert os.path.exists(my_new_path)

def test_custom_args(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path):
    cmd_init = CmdRunInit(fx_get_sub_parser)
    sys.argv.extend(["-a", "test author", "-ae", "test@example.com", "-u", "hello.com", "-l", "My License"])
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    with open(constants.SDK_SETTINGS_FILE_PATH) as f:
        settings_json = json.load(f)
        assert settings_json.get("codegen").get("setup").get("author") == "test author"
        assert settings_json.get("codegen").get("setup").get("author_email") == "test@example.com"
        assert settings_json.get("codegen").get("setup").get("url") == "hello.com"
        assert settings_json.get("codegen").get("setup").get("license") == "My License"

def test_internal_use(fx_mk_temp_dir, fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path):
    cmd_init = CmdRunInit(fx_get_sub_parser)
    sys.argv.extend(["-i"])
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    with open(constants.SDK_SETTINGS_FILE_PATH) as f:
        settings_json = json.load(f)
        assert settings_json.get("codegen").get("setup").get("author") == constants.INIT_INTERNAL_AUTHOR
        assert settings_json.get("codegen").get("setup").get("author_email") == constants.INIT_INTERNAL_AUTHOR_EMAIL
        assert settings_json.get("codegen").get("setup").get("url") == constants.INIT_INTERNAL_URL
        assert settings_json.get("codegen").get("setup").get("license") == constants.INIT_INTERNAL_LICENSE
        assert settings_json.get("codegen").get("setup").get("long_description") == constants.INIT_INTERNAL_LONG_DESC
        assert settings_json.get("codegen").get("copyright") == constants.INIT_INTERNAL_COPYRIGHT
        assert u"Copyright © IBM Corporation {0}" in settings_json.get("codegen").get("license_content")
        assert settings_json.get("docgen").get("supported_app") == True
