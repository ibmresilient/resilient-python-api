#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import os
from resilient_sdk.cmds import base_cmd, CmdCodegen
from resilient_sdk.util import helpers
from tests.shared_mock_data import mock_paths


def test_cmd_codegen(fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)

    assert isinstance(cmd_codegen, base_cmd.BaseCmd)
    assert cmd_codegen.CMD_NAME == "codegen"
    assert cmd_codegen.CMD_HELP == "Generate boilerplate code to start developing an Extension"
    assert cmd_codegen.CMD_USAGE == """
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
    $ resilient-sdk codegen -p <path_current_package> --reload --workflow 'new_wf_to_add'"""
    assert cmd_codegen.CMD_DESCRIPTION == "Generate boilerplate code to start developing an Extension"
    assert cmd_codegen.CMD_USE_COMMON_PARSER_ARGS is True

    args = cmd_codegen.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_render_jinja_mapping(fx_mk_temp_dir):

    mock_jinja_data = {
        "functions": [{"x_api_name": "fn_mock_function_1"}, {"x_api_name": "fn_mock_function_2"}]
    }

    jinja_env = helpers.setup_jinja_env("data/codegen/templates/package_template")

    jinja_mapping_dict = {
        "setup.py": ("setup.py.jinja2", {}),
        "tox.ini": ("tox.ini.jinja2", {}),
        "test_package": {
            "__init__.py": ("package/__init__.py.jinja2", {}),
            "util": {
                "config.py": ("package/util/config.py.jinja2", {}),
                "customize.py": ("package/util/customize.py.jinja2", mock_jinja_data)
            }
        }
    }

    CmdCodegen.render_jinja_mapping(jinja_mapping_dict, jinja_env, mock_paths.TEST_TEMP_DIR)

    files_in_dir = os.listdir(mock_paths.TEST_TEMP_DIR)

    assert "setup.py" in files_in_dir
    assert "tox.ini" in files_in_dir
    assert "test_package" in files_in_dir

    files_in_test_package = os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package"))
    assert "__init__.py" in files_in_test_package
    assert "util" in files_in_test_package

    files_in_util = os.listdir(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", "util"))
    assert "config.py" in files_in_util
    assert "customize.py" in files_in_util

    customize_py = helpers.read_file(os.path.join(mock_paths.TEST_TEMP_DIR, "test_package", "util", "customize.py"))
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