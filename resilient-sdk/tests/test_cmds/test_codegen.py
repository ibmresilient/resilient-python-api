#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import sys
import shutil
import pytest
from resilient_sdk.cmds import base_cmd, CmdCodegen
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util.sdk_exception import SDKException
from tests import helpers
from tests.shared_mock_data import mock_paths

EXPECTED_FILES_ROOT_DIR = [
    'Dockerfile',
    'MANIFEST.in',
    'README.md',
    'apikey_permissions.txt',
    'data',
    'doc',
    'entrypoint.sh',
    'fn_main_mock_integration',
    'icons',
    'payload_samples',
    'setup.py',
    'tests',
    'tox.ini'
]

EXPECTED_FILES_DATA_DIR = ['wf_mock_workflow_one.md', 'wf_mock_workflow_two.md']
EXPECTED_FILES_DOC_DIR = ['screenshots']
EXPECTED_FILES_DOC_SCREENSHOTS_DIR = ['main.png']
EXPECTED_FILES_PACKAGE_DIR = ['LICENSE', '__init__.py', 'components', 'util']
EXPECTED_FILES_PACKAGE_COMPONENTS_DIR = ['__init__.py', 'funct_mock_function_one.py', 'funct_mock_function_two.py']
EXPECTED_FILES_PACKAGE_UTIL_DIR = ['__init__.py', 'config.py', 'customize.py', 'data', 'selftest.py']
EXPECTED_FILES_PACKAGE_UTIL_DATA_DIR = ['export.res']
EXPECTED_FILES_ICONS_DIR = ['app_logo.png', 'company_logo.png']
EXPECTED_FILES_TESTS_DIR = ['test_funct_mock_function_one.py', 'test_funct_mock_function_two.py']
EXPECTED_FILES_PAYLOAD_SAMPLES_DIR = ['mock_function_one', 'mock_function_two']
EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR = ['mock_json_endpoint_fail.json', 'mock_json_endpoint_success.json', 'mock_json_expectation_fail.json',
                                              'mock_json_expectation_success.json', 'output_json_example.json', 'output_json_schema.json']


def general_test_package_structure(package_name, package_path):
    """
    This is a general function that the tests for gen_package and reload_package
    call to make sure that the expected files are created in each directory
    """
    assert helpers.verify_expected_list(EXPECTED_FILES_ROOT_DIR, os.listdir(package_path))
    assert helpers.verify_expected_list(EXPECTED_FILES_DATA_DIR, os.listdir(os.path.join(package_path, "data")))
    assert helpers.verify_expected_list(EXPECTED_FILES_DOC_DIR, os.listdir(os.path.join(package_path, "doc")))
    assert helpers.verify_expected_list(EXPECTED_FILES_DOC_SCREENSHOTS_DIR, os.listdir(os.path.join(package_path, "doc", "screenshots")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_DIR, os.listdir(os.path.join(package_path, package_name)))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_COMPONENTS_DIR, os.listdir(os.path.join(package_path, package_name, "components")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_UTIL_DIR, os.listdir(os.path.join(package_path, package_name, "util")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PACKAGE_UTIL_DATA_DIR, os.listdir(os.path.join(package_path, package_name, "util", "data")))
    assert helpers.verify_expected_list(EXPECTED_FILES_ICONS_DIR, os.listdir(os.path.join(package_path, "icons")))
    assert helpers.verify_expected_list(EXPECTED_FILES_TESTS_DIR, os.listdir(os.path.join(package_path, "tests")))

    # Test payload_samples were generated for each fn
    files_in_payload_samples = sorted(os.listdir(os.path.join(package_path, "payload_samples")))
    assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_DIR, files_in_payload_samples)

    for file_name in files_in_payload_samples:
        assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR, os.listdir(os.path.join(package_path, "payload_samples", file_name)))


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


def test_add_payload_samples():

    mock_fn_name = "Mock Function Name"
    mock_jinja_data = {"mock": "data"}
    mock_mapping_dict = {package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR: {}}
    mock_mapping_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR][mock_fn_name] = {}
    CmdCodegen.add_payload_samples(mock_mapping_dict, mock_fn_name, mock_jinja_data)

    for f in EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR:
        assert isinstance(mock_mapping_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR][mock_fn_name][f], tuple)
        assert mock_mapping_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR][mock_fn_name][f][1] == mock_jinja_data


def test_gen_function():
    # TODO:
    pass


def test_gen_package(fx_get_sub_parser, fx_cmd_line_args_codegen_package, fx_mk_temp_dir, fx_add_dev_env_var):
    """
    This tests that when a package is generated with codegen
    that each of the EXPECTED_FILES exist in each directory.
    This test is NOT concerned about the contents of each file,
    just that it exists
    """
    output_path = mock_paths.TEST_TEMP_DIR

    # Add paths to an output base and an export.res file
    sys.argv.extend(["-o", output_path])
    sys.argv.extend(["-e", mock_paths.MOCK_EXPORT_RES])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen._gen_package(args)

    package_name = args.package
    package_path = os.path.join(output_path, args.package)
    general_test_package_structure(package_name, package_path)


def test_reload_package(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_codegen_reload):
    """
    This tests that when a package is reloaded with codegen --reload
    that each of the EXPECTED_FILES exist and also the additional 'Additional Mock Rule'
    and its related Workflow which has a Function is also added to the package
    """
    
    output_path = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_path", "fn_main_mock_integration-1.1.0")
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    shutil.move(fx_copy_fn_main_mock_integration[1], output_path)

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = output_path

    # Add path to a mock export.res file
    sys.argv.extend(["-e", mock_paths.MOCK_RELOAD_EXPORT_RES])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    path_package_reloaded = cmd_codegen._reload_package(args)

    # This is really getting the import definition from the new data/export.res file, so tests that as well
    import_definition = package_helpers.get_import_definition_from_customize_py(os.path.join(path_package_reloaded, mock_integration_name, package_helpers.PATH_CUSTOMIZE_PY))

    res_objs = sdk_helpers.get_from_export(import_definition,
                                           rules=["Additional Mock Rule", "Mock Manual Rule"],
                                           functions=["additional_mock_function", "mock_function_one"],
                                           workflows=["additional_mock_workflow", "mock_workflow_one"])

    # Assert the general structure of the reloaded package
    general_test_package_structure(mock_integration_name, path_package_reloaded)

    # Assert the additional rule, function and workflow were added
    assert helpers.verify_expected_list(["Additional Mock Rule", "Mock Manual Rule"], [o.get("x_api_name") for o in res_objs.get("rules")])
    assert helpers.verify_expected_list(["additional_mock_function", "mock_function_one"], [o.get("x_api_name") for o in res_objs.get("functions")])
    assert helpers.verify_expected_list(["additional_mock_workflow", "mock_workflow_one"], [o.get("x_api_name") for o in res_objs.get("workflows")])

    # Assert a new components file is created
    expected_component_files = EXPECTED_FILES_PACKAGE_COMPONENTS_DIR + ["funct_additional_mock_function.py"]
    assert helpers.verify_expected_list(expected_component_files, os.listdir(os.path.join(path_package_reloaded, mock_integration_name, "components")))

    # Assert a new tests file is created
    expected_test_files = EXPECTED_FILES_TESTS_DIR + ["test_funct_additional_mock_function.py"]
    assert helpers.verify_expected_list(expected_test_files, os.listdir(os.path.join(path_package_reloaded, "tests")))

    # Assert a new md file is created in data dir
    expected_workflow_files = EXPECTED_FILES_DATA_DIR + ["wf_additional_mock_workflow.md"]
    assert helpers.verify_expected_list(expected_workflow_files, os.listdir(os.path.join(path_package_reloaded, "data")))


def test_forget_reload_flag(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    """
    This tests that it you forget the --reload flag you get an error
    """
    output_path = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_path", "fn_main_mock_integration-1.1.0")
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    shutil.move(fx_copy_fn_main_mock_integration[1], output_path)

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = output_path

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]

    with pytest.raises(SDKException, match=r"already exists. Add --reload flag to regenerate it"):
        cmd_codegen._gen_package(args)


def test_execute_command():
    # TODO
    pass