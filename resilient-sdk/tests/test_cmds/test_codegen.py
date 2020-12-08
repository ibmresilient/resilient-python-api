#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
from resilient_sdk.cmds import base_cmd, CmdCodegen
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers
from tests.shared_mock_data import mock_paths


def test_cmd_codegen(fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)

    assert isinstance(cmd_codegen, base_cmd.BaseCmd)
    assert cmd_codegen.CMD_NAME == "codegen"
    assert cmd_codegen.CMD_HELP == "Generate boilerplate code to start developing an app"
    assert cmd_codegen.CMD_USAGE == """
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
    $ resilient-sdk codegen -p <path_current_package> --reload --workflow 'new_wf_to_add'"""
    assert cmd_codegen.CMD_DESCRIPTION == "Generate boilerplate code to start developing an app"
    assert cmd_codegen.CMD_ADD_PARSERS == ["res_obj_parser", "io_parser"]

    args = cmd_codegen.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_cmd_codegen_args_parser(fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)

    assert cmd_codegen.parser._optionals.title == "options"

    args = cmd_codegen.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"
    assert args.messagedestination == ["fn_main_mock_integration"]
    assert args.function == ["mock_function_one"]
    assert args.rule == ["Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination"]
    assert args.workflow == ["mock_workflow_one", "mock_workflow_two"]
    assert args.field == ["mock_field_number", "mock_field_number", "mock_field_text_area"]
    assert args.artifacttype == ["mock_artifact_2", "mock_artifact_type_one"]
    assert args.datatable == ["mock_data_table"]
    assert args.task == ["mock_custom_task_one", "mock_cusom_task__________two"]
    assert args.script == ["Mock Script One"]


def test_render_jinja_mapping(fx_mk_temp_dir):

    mock_jinja_data = {
        "functions": [{"x_api_name": "fn_mock_function_1"}, {"x_api_name": "fn_mock_function_2"}],
        "export_data": {"server_version": {"version": "35.0.0"}}
    }

    jinja_env = sdk_helpers.setup_jinja_env("data/codegen/templates/package_template")

    jinja_mapping_dict = {
        "MANIFEST.in": ("MANIFEST.in.jinja2", mock_jinja_data),
        "README.md": ("README.md.jinja2", mock_jinja_data),
        "setup.py": ("setup.py.jinja2", mock_jinja_data),
        "tox.ini": ("tox.ini.jinja2", mock_jinja_data),
        "Dockerfile": ("Dockerfile.jinja2", mock_jinja_data),
        "entrypoint.sh": ("entrypoint.sh.jinja2", mock_jinja_data),
        "apikey_permissions.txt": ("apikey_permissions.txt.jinja2", mock_jinja_data),
        "data": {},
        "icons": {
            "company_logo.png": package_helpers.PATH_DEFAULT_ICON_COMPANY_LOGO,
            "app_logo.png": package_helpers.PATH_DEFAULT_ICON_EXTENSION_LOGO,
        },
        "doc": {
            "screenshots": {
                "main.png": package_helpers.PATH_DEFAULT_SCREENSHOT
            }
        },
        "test_package": {
            "__init__.py": ("package/__init__.py.jinja2", mock_jinja_data),
            "LICENSE": ("package/LICENSE.jinja2", mock_jinja_data),

            "components": {
                "__init__.py": ("package/components/__init__.py.jinja2", mock_jinja_data),
            },
            "util": {
                "data": {
                    "export.res": ("package/util/data/export.res.jinja2", mock_jinja_data)
                },
                "__init__.py": ("package/util/__init__.py.jinja2", mock_jinja_data),
                "config.py": ("package/util/config.py.jinja2", mock_jinja_data),
                "customize.py": ("package/util/customize.py.jinja2", mock_jinja_data),
                "selftest.py": ("package/util/selftest.py.jinja2", mock_jinja_data),
            }
        }
    }

    CmdCodegen.render_jinja_mapping(jinja_mapping_dict, jinja_env, mock_paths.TEST_TEMP_DIR, mock_paths.TEST_TEMP_DIR)

    files_in_dir = sorted(os.listdir(mock_paths.TEST_TEMP_DIR))
    assert files_in_dir == ['Dockerfile', 'MANIFEST.in', 'README.md', 'apikey_permissions.txt', 'data', 'doc', 'entrypoint.sh', 'icons', 'setup.py', 'test_package', 'tox.ini']

    files_in_icons_dir = sorted(os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "icons")))
    assert files_in_icons_dir == ['app_logo.png', 'company_logo.png']

    files_in_test_package = sorted(os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package")))
    assert files_in_test_package == ['LICENSE', '__init__.py', 'components', 'util']

    files_in_util = sorted(os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", "util")))
    assert files_in_util == ['__init__.py', 'config.py', 'customize.py', 'data', 'selftest.py']

    files_in_util_data = sorted(
        os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", package_helpers.PATH_UTIL_DATA_DIR)))
    assert files_in_util_data == ['export.res']

    files_in_components = sorted(os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", "components")))
    assert files_in_components == ['__init__.py']

    customize_py = sdk_helpers.read_file(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", "util", "customize.py"))
    assert '        "functions": [u"fn_mock_function_1", u"fn_mock_function_2"],\n' in customize_py


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


def test_execute_command():
    # TODO
    pass