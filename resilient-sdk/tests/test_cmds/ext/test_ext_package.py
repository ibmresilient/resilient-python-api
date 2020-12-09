#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import sys
import zipfile
from resilient_sdk.cmds import CmdExtPackage as CmdPackage
from resilient_sdk.util import sdk_helpers
from tests.shared_mock_data import mock_paths

EXPECTED_FILES_APP_ZIP = ['app.json', 'export.res', 'fn_main_mock_integration-1.0.0.tar.gz']


def test_setup():
    # TODO
    pass


def test_execute_command(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_package):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Package the app
    cmd_package = CmdPackage(fx_get_sub_parser)
    args = cmd_package.parser.parse_known_args()[0]
    path_the_app_zip = cmd_package.execute_command(args)

    # Test app.zip contents
    assert zipfile.is_zipfile(path_the_app_zip)
    with zipfile.ZipFile((path_the_app_zip), 'r') as app_zip:
        assert EXPECTED_FILES_APP_ZIP == sorted(app_zip.namelist())

    # Test app.zip/app.json contents
    app_json_contents = sdk_helpers.read_zip_file(path_the_app_zip, "app.json")
    mock_app_json_contents = sdk_helpers.read_file(mock_paths.MOCK_APP_ZIP_APP_JSON)[0]
    assert app_json_contents == mock_app_json_contents

    # Test app.zip/export.res contents
    export_res_contents = sdk_helpers.read_zip_file(path_the_app_zip, "export.res")
    mock_export_res_contents = sdk_helpers.read_file(mock_paths.MOCK_APP_ZIP_EXPORT_RES)[0]
    assert export_res_contents == mock_export_res_contents
