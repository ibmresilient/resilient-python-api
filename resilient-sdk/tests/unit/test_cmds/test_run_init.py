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
import tests.shared_mock_data.sdk_mock_paths as mock_paths


def test_cmd_init_setup(fx_get_sub_parser, fx_cmd_line_args_init):
    """
    Test that basic information about the command gets initialized properly, like name, help, usage, and description
    """
    cmd_init = CmdRunInit(fx_get_sub_parser)

    assert isinstance(cmd_init, base_cmd.BaseCmd)
    assert cmd_init.CMD_NAME == "init"
    assert cmd_init.CMD_HELP == "Generates sdk_settings.json file to store default settings and generates app.config file to store connection details. \
        Providing a flag will override the default paths."
    assert cmd_init.CMD_USAGE == """
    $ resilient-sdk init
    $ resilient-sdk init --settings <path to settings json>
    $ resilient-sdk init --settings <path to settings json> -a/--author you@example.com
    $ resilient-sdk init -c/--config <path to app.config>
    $ resilient-sdk init --settings <path to settings json> -c/--config <path to app.config>
    """
    assert cmd_init.CMD_DESCRIPTION == cmd_init.CMD_HELP

def test_file_creation(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_mock_config_file_path):
    """
    Test creating an SDK settings file and a config file in default locations as defined in constants.py with `resilient-sdk init`
    """
    cmd_init = CmdRunInit(fx_get_sub_parser)
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    assert os.path.exists(constants.SDK_SETTINGS_FILE_PATH)
    assert os.path.exists(constants.PATH_RES_DEFAULT_APP_CONFIG)

@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_check_overwrite_py3(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_create_mock_settings_file, caplog):
    """ 
    Test entering different values to specify whether or not to overwrite the specified file
    """
    # Check if default, "y" to overwrite returns true
    cmd_init = CmdRunInit(fx_get_sub_parser)
    ret = cmd_init._check_overwrite(constants.SDK_SETTINGS_FILE_PATH, True)
    assert ret is True

    # Check if specifying "n" to overwrite returns false
    with patch("resilient_sdk.cmds.run_init.input", return_value="n"):
        ret = cmd_init._check_overwrite(constants.SDK_SETTINGS_FILE_PATH, False)
        assert ret is False


@pytest.mark.skipif(sys.version_info.major > 2, reason="requires python 2")
def test_check_overwrite_py2(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_create_mock_settings_file, caplog):
    """ 
    Test entering 'n' to skip overwriting a file
    """
    with patch("resilient_sdk.cmds.run_init.raw_input", return_value="n"):
        cmd_init = CmdRunInit(fx_get_sub_parser)
        ret = cmd_init._check_overwrite(constants.SDK_SETTINGS_FILE_PATH, False)
        assert ret is False

def test_render_template(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_mock_config_file_path):
    """
    Test for private method to render a specific template. So far, the init command can create app.config and sdk_settings.json
    so those are the two tests to try out here
    """
    # check sdk settings file
    cmd_init = CmdRunInit(fx_get_sub_parser)
    template_args = {
                "author": "IBM dev",
                "author_email": "a@example.com",
                "url": "test.com",
                "license": "MIT",
                "supported_app": "true",
                "long_description": "This is a long description",
                "license_content": "abcdefg",
                "copyright": "IBM 2024"
            }
    cmd_init._render_template(constants.SETTINGS_TEMPLATE_NAME, constants.SDK_SETTINGS_FILE_PATH, template_args)
    with open(constants.SDK_SETTINGS_FILE_PATH) as f:
        settings_json = json.load(f)
        assert settings_json.get("codegen").get("setup").get("author_email") == "a@example.com"
        assert settings_json.get("codegen").get("setup").get("url") == "test.com"
        assert settings_json.get("codegen").get("setup").get("long_description") == "This is a long description"
        assert settings_json.get("codegen").get("copyright") == "IBM 2024"
        assert settings_json.get("docgen").get("supported_app") == True

    # Check config file
    cmd_init._render_template(constants.CONFIG_TEMPLATE_NAME, constants.PATH_RES_DEFAULT_APP_CONFIG, {})
    with open(constants.PATH_RES_DEFAULT_APP_CONFIG) as f:
        contents = f.read()
        assert "[resilient]\nhost=my_soar_instance.ibm.com" in contents
        assert "cafile=false" in contents

def test_default_settings(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_mock_config_file_path):
    """
    Test filling out sdk_settings.json with default values (because none are passed in via the command line)
    """
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

def test_custom_settings_path(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_config_file_path, fx_reset_argv):
    """
    Test supplying a custom filepath for the settings file
    """
    cmd_init = CmdRunInit(fx_get_sub_parser)
    my_new_path = os.path.join(mock_paths.TEST_TEMP_DIR, "my_test.json")
    sys.argv.extend(["--settings", my_new_path])
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    assert os.path.exists(my_new_path)

def test_custom_app_config_path(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_reset_argv):
    """
    Test supplying a custom filepath for the app file
    """
    cmd_init = CmdRunInit(fx_get_sub_parser)
    my_new_path =os.path.join(mock_paths.TEST_TEMP_DIR, "app.config.test")
    sys.argv.extend(["-c", my_new_path])
    args = cmd_init.parser.parse_known_args()[0]
    cmd_init.execute_command(args)
    assert os.path.exists(my_new_path)

def test_custom_args(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_mock_config_file_path, fx_reset_argv):
    """
    Test customizing the sdk_settings.json file with custom fields specified by the command line arguments
    """
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

def test_internal_use(fx_get_sub_parser, fx_cmd_line_args_init, fx_mock_settings_file_path, fx_mock_config_file_path, fx_reset_argv):
    """
    Test the internal flag that supplies the default IBM Supported fields for apps developed by the Hydra team
    """
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
