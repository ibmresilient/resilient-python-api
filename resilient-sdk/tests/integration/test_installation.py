#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import sys
from resilient_sdk.cmds import CmdExtPackage as CmdPackage
from resilient_sdk.util import sdk_helpers
from tests import helpers as test_helpers


def test_installation(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_package):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Package the app
    cmd_package = CmdPackage(fx_get_sub_parser)
    args = cmd_package.parser.parse_known_args()[0]
    path_the_app_zip = cmd_package.execute_command(args)

    # Connect to test resilient
    res_client = sdk_helpers.get_resilient_client()

    # Test uploading + installing the .zip
    upload_res = test_helpers.upload_app_zip(res_client, path_the_app_zip)
    assert upload_res.status_code == 200

    install_res = test_helpers.install_app_zip(res_client, upload_res.json())
    assert install_res.get("status") == "installed"
