#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import sys
import os
import shutil
import pytest
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.cmds import base_cmd, CmdDev
from tests.shared_mock_data import mock_paths


def test_cmd_dev(fx_get_sub_parser, fx_cmd_line_args_dev_set_version):
    cmd_dev = CmdDev(fx_get_sub_parser)

    assert isinstance(cmd_dev, base_cmd.BaseCmd)
    assert cmd_dev.CMD_NAME == "dev"
    assert cmd_dev.CMD_HELP == "Unsupported functionality used to help develop an app"
    assert cmd_dev.CMD_USAGE == """
    $ resilient-sdk dev -p <path_to_package> --set-version 36.0.0"""
    assert cmd_dev.CMD_DESCRIPTION == "WARNING: Use the functionality of 'dev' at your own risk"

    args = cmd_dev.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_set_version_bad_version(fx_get_sub_parser, fx_cmd_line_args_dev_set_bad_version):
    cmd_dev = CmdDev(fx_get_sub_parser)
    args = cmd_dev.parser.parse_known_args()[0]

    with pytest.raises(SDKException, match=r"is not a valid version"):
        CmdDev._set_version(args)


def test_set_version(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_dev_set_version):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Parse the setup.py file
    path_setup_py_file = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_SETUP_PY)
    setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

    # Get customize.py ImportDefinition
    path_customize_py = package_helpers.get_configuration_py_file_path("customize", setup_py_attributes)
    customize_py_import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py)

    # Get the old_version
    old_version = customize_py_import_definition["server_version"]["version"]
    assert old_version == "36.0.0"

    # Run _set_version
    cmd_dev = CmdDev(fx_get_sub_parser)
    args = cmd_dev.parser.parse_known_args()[0]
    cmd_dev._set_version(args)

    # Get the new_version
    customize_py_import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py)
    new_version = customize_py_import_definition["server_version"]["version"]
    assert new_version == "35.0.0"
