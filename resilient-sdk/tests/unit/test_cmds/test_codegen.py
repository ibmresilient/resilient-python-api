#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import os
import shutil
import sys
from pathlib import Path

import pytest
from mock import patch
from packaging.version import parse as parse_version
from resilient_sdk.cmds import CmdCodegen, base_cmd
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
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
PB_MD_FILE = "pb_test_resilient_sdk.md"
EXPECTED_FILES_DATA_DIR = ['wf_mock_workflow_one.md', 'wf_mock_workflow_two.md']
EXPECTED_FILES_DOC_DIR = ['screenshots']
EXPECTED_FILES_DOC_SCREENSHOTS_DIR = ['main.png']
EXPECTED_FILES_PACKAGE_DIR = ['LICENSE', '__init__.py', 'components', 'util', 'poller', 'lib']
EXPECTED_FILES_PACKAGE_COMPONENTS_DIR = ['__init__.py', 'funct_mock_function_one.py', 'funct_mock_function_two.py']
EXPECTED_FILES_PACKAGE_UTIL_DIR = ['__init__.py', 'config.py', 'customize.py', 'data', 'selftest.py']
EXPECTED_FILES_PACKAGE_UTIL_DATA_DIR = ['export.res']
EXPECTED_FILES_ICONS_DIR = ['app_logo.png', 'company_logo.png']
EXPECTED_FILES_TESTS_DIR = ['test_funct_mock_function_one.py', 'test_funct_mock_function_two.py']
EXPECTED_FILES_PAYLOAD_SAMPLES_DIR = ['mock_function_one', 'mock_function_two']
EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR = ['output_json_example.json', 'output_json_schema.json']
EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR_DEV = ['output_json_example.json', 'output_json_schema.json']
# TODO: comment back in when we have logic to use the mock_json files
"""
EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR_DEV = ['mock_json_endpoint_fail.json', 'mock_json_endpoint_success.json', 'mock_json_expectation_fail.json',
                                                  'mock_json_expectation_success.json', 'output_json_example.json', 'output_json_schema.json']
"""
EXPECTED_FILES_POLLER_DIR = ["__init__.py", "poller.py"]
EXPECTED_FILES_POLLER_DATA_DIR = ["soar_create_case.jinja", "soar_update_case.jinja", "soar_close_case.jinja"]
EXPECTED_FILES_LIB_DIR = ["__init__.py", "app_common.py"]

def general_test_package_structure(package_name, package_path, poller=False):
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
        if sdk_helpers.is_env_var_set(constants.ENV_VAR_DEV):
            assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR_DEV, os.listdir(os.path.join(package_path, "payload_samples", file_name)))
        else:
            assert helpers.verify_expected_list(EXPECTED_FILES_PAYLOAD_SAMPLES_FN_NAME_DIR, os.listdir(os.path.join(package_path, "payload_samples", file_name)))

    if poller:
        assert helpers.verify_expected_list(EXPECTED_FILES_POLLER_DIR, os.listdir(os.path.join(package_path, package_name, "poller")))
        assert helpers.verify_expected_list(EXPECTED_FILES_POLLER_DATA_DIR, os.listdir(os.path.join(package_path, package_name, "poller", "data")))
        assert helpers.verify_expected_list(EXPECTED_FILES_LIB_DIR, os.listdir(os.path.join(package_path, package_name, "lib")))


def compare_playbooks_md_file(package_name, package_path):
    # Compares pb_test_resilient_sdk.md file generated by gen_package with the one in the mock_integration
    assert PB_MD_FILE in os.listdir(os.path.join(package_path, "data"))
    with open(os.path.join(mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION, "data", PB_MD_FILE)) as expected_md_file:
        expected_md = expected_md_file.readlines()
    with open(os.path.join(package_path, "data", PB_MD_FILE)) as expected_md_file:
        generated_md = expected_md_file.readlines()

    len(generated_md) > 0 # checking if file is not empty
    assert len(expected_md) == len(generated_md) 
    
    expected_md, generated_md = expected_md[7:], generated_md[7:] # removing the first 7 lines of the file as resilient_sdk version can change
    for exp, gen in zip(expected_md, generated_md):
        assert exp == gen


def test_cmd_codegen(fx_get_sub_parser, fx_cmd_line_args_codegen_package):
    cmd_codegen = CmdCodegen(fx_get_sub_parser)

    assert isinstance(cmd_codegen, base_cmd.BaseCmd)
    assert cmd_codegen.CMD_NAME == "codegen"
    assert cmd_codegen.CMD_HELP == "Generates boilerplate code used to begin developing an app."
    assert cmd_codegen.CMD_USAGE == """
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two' -i 'custom incident type'
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two' --settings <path_to_custom_sdk_settings_file>
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' -c '/usr/custom_app.config'
    $ resilient-sdk codegen -p <path_current_package> --reload --workflow 'new_wf_to_add'
    $ resilient-sdk codegen -p <path_current_package> --poller
    $ resilient-sdk codegen -p <path_current_package> --gather-results
    $ resilient-sdk codegen -p <path_current_package> --gather-results '/usr/custom_app.log' -f 'func_one' 'func_two'"""
    assert cmd_codegen.CMD_DESCRIPTION == cmd_codegen.CMD_HELP
    assert cmd_codegen.CMD_ADD_PARSERS == ["app_config_parser", "res_obj_parser", "io_parser", constants.SDK_SETTINGS_PARSER_NAME]

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
    assert args.incidenttype == [u"mock_incidenttype_Āā", u"mock incident type one"]


def test_render_jinja_mapping(fx_mk_temp_dir):

    mock_jinja_data = {
        "functions": [{"x_api_name": "fn_mock_function_1"}, {"x_api_name": "fn_mock_function_2"}],
        "export_data": {"server_version": {"version": "35.0.0"}}
    }

    jinja_env = sdk_helpers.setup_jinja_env(constants.PACKAGE_TEMPLATE_PATH)

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
    assert set(['        "functions": [\n','            u"fn_mock_function_1",\n','            u"fn_mock_function_2"\n','        ],\n']).issubset(set(customize_py))


def test_gen_package_with_playbooks(fx_get_sub_parser, fx_reset_argv, fx_mk_temp_dir, fx_add_dev_env_var):
    """
    This tests that when a package is generated with codegen
    that each of the EXPECTED_FILES exist in each directory.
    This test is NOT concerned about the contents of each file,
    just that it exists
    """
    output_path = mock_paths.TEST_TEMP_DIR
    constants.CURRENT_SOAR_SERVER_VERSION = parse_version("46.0") # setting SOAR server version to 46.0

    # Add paths to an output base and an export.res file
    sys.argv.extend(["codegen"])
    sys.argv.extend(["-p", "test_resilient_sdk_with_playbooks"])
    sys.argv.extend(["-pb", "test_resilient_sdk"])
    sys.argv.extend(["-f", "create_a_scheduled_rule", "scheduled_rule_pause"])
    sys.argv.extend(["-o", output_path])
    sys.argv.extend(["-e", os.path.join(mock_paths.SHARED_MOCK_DATA_DIR, mock_paths.RESILIENT_API_DATA, "export-with-playbook.JSON")])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen._gen_package(args)

    package_name = args.package
    package_path = os.path.join(output_path, args.package)
    compare_playbooks_md_file(package_name, package_path)
    
    constants.CURRENT_SOAR_SERVER_VERSION = None


def test_run_tests_with_settings_file(fx_get_sub_parser, fx_mk_temp_dir, fx_mock_res_client, fx_cmd_line_args_codegen_package):
    with patch("resilient_sdk.cmds.codegen.sdk_helpers.get_resilient_client") as mock_client:

        mock_client.return_value = fx_mock_res_client
        output_path = mock_paths.TEST_TEMP_DIR

        # Add paths to an output base and an export.res file
        sys.argv.extend(["--settings", mock_paths.MOCK_SDK_SETTINGS_PATH, "--output", mock_paths.TEST_TEMP_DIR])

        cmd_codegen = CmdCodegen(fx_get_sub_parser)
        args = cmd_codegen.parser.parse_known_args()[0]
        cmd_codegen.execute_command(args)

        setup_py = sdk_helpers.read_file(os.path.join(mock_paths.TEST_TEMP_DIR, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, "setup.py"))
        assert '    license="MIT",\n' in setup_py
        assert '    author="author name",\n' in setup_py
        assert '    author_email="you@example.com",\n' in setup_py
        assert '    url="example.com",\n' in setup_py
        assert '    long_description="""<<CHANGE ME>> this is an example long description""",\n' in setup_py

        license = sdk_helpers.read_file(os.path.join(mock_paths.TEST_TEMP_DIR, mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME,
                        mock_paths.MOCK_INT_FN_MAIN_MOCK_INTEGRATION_NAME, "LICENSE"))
        assert 'This is a test license.' in license


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
        ("script", "scripts"),
        ("playbook", "playbooks")
    ]

    merged_args = CmdCodegen.merge_codegen_params(old_params, args, mapping_tuples)

    assert len(merged_args.function) == 2
    assert "new_fn_1" in merged_args.function
    assert "new_fn_2" in merged_args.function
    assert "rule 3" in merged_args.rule
    assert "script 1" in merged_args.script
    assert merged_args.playbook == []


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
    sys.argv.extend(["--poller"])

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
                                           functions=["additional_mock_function", "mock_function_one", "funct_new_mock_function", "func_new_mock_function"],
                                           workflows=["additional_mock_workflow", "mock_workflow_one", "wf_new_mock_workflow"])

    # Assert the general structure of the reloaded package
    general_test_package_structure(mock_integration_name, path_package_reloaded)

    # Assert the additional rule, function and workflow were added
    assert helpers.verify_expected_list(["Additional Mock Rule", "Mock Manual Rule"], [o.get("x_api_name") for o in res_objs.get("rules")])
    assert helpers.verify_expected_list(["additional_mock_function", "mock_function_one", "funct_new_mock_function", "func_new_mock_function" ], [o.get("x_api_name") for o in res_objs.get("functions")])
    assert helpers.verify_expected_list(["additional_mock_workflow", "mock_workflow_one", "wf_new_mock_workflow"], [o.get("x_api_name") for o in res_objs.get("workflows")])

    # Assert a new components file is created
    expected_component_files = EXPECTED_FILES_PACKAGE_COMPONENTS_DIR + ["funct_additional_mock_function.py"]
    assert helpers.verify_expected_list(expected_component_files, os.listdir(os.path.join(path_package_reloaded, mock_integration_name, "components")))

    # Assert a new components file with prefix 'funct_' is created
    expected_component_files = ["funct_new_mock_function.py"]
    assert helpers.verify_expected_list(expected_component_files, os.listdir(os.path.join(path_package_reloaded, mock_integration_name, "components")))

    # Assert a new components file with prefix 'func_' is created
    expected_component_files = ["func_new_mock_function.py"]
    assert helpers.verify_expected_list(expected_component_files, os.listdir(
        os.path.join(path_package_reloaded, mock_integration_name, "components")))

    # Assert a new tests file is created
    expected_test_files = EXPECTED_FILES_TESTS_DIR + ["test_funct_additional_mock_function.py"]
    assert helpers.verify_expected_list(expected_test_files, os.listdir(os.path.join(path_package_reloaded, "tests")))

    # Assert a new tests file including 'func_' is created.
    expected_test_files = ["test_func_new_mock_function.py"]
    assert helpers.verify_expected_list(expected_test_files, os.listdir(os.path.join(path_package_reloaded, "tests")))

    # Assert a new md file is created in data dir
    expected_workflow_files = EXPECTED_FILES_DATA_DIR + ["wf_additional_mock_workflow.md"]
    assert helpers.verify_expected_list(expected_workflow_files, os.listdir(os.path.join(path_package_reloaded, "data")))

    # Assert a new md file with 'wf_' is created in data dir
    expected_workflow_files = ["wf_new_mock_workflow.md"]
    assert helpers.verify_expected_list(expected_workflow_files, os.listdir(os.path.join(path_package_reloaded, "data")))

    # Remove files from generated package path and recreate without prefix or substring of 'funct_' or 'wf_'.
    os.remove(os.path.join(path_package_reloaded, mock_integration_name, "components",
                           "funct_additional_mock_function.py"))
    Path(os.path.join(path_package_reloaded, mock_integration_name, "components",
                           "additional_mock_function.py")).touch()
    os.remove(os.path.join(path_package_reloaded, "tests", "test_funct_additional_mock_function.py"))
    Path(os.path.join(path_package_reloaded, "tests", "test_additional_mock_function.py")).touch()
    os.remove(os.path.join(path_package_reloaded, "data", "wf_additional_mock_workflow.md"))
    Path(os.path.join(path_package_reloaded, "data", "additional_mock_workflow.md")).touch()

    # Get modification time for workflow file "wf_mock_workflow_one.md" in seconds since the epoch.'
    wf_modified_time = os.path.getmtime(os.path.join(path_package_reloaded, "data", "wf_mock_workflow_one.md"))

    # Perform another test reload.
    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    path_package_reloaded = cmd_codegen._reload_package(args)

    # This is really getting the import definition from the new data/export.res file, so tests that as well
    import_definition = package_helpers.get_import_definition_from_customize_py(os.path.join(path_package_reloaded, mock_integration_name, package_helpers.PATH_CUSTOMIZE_PY))

    res_objs = sdk_helpers.get_from_export(import_definition,
                                           rules=["Additional Mock Rule", "Mock Manual Rule"],
                                           functions=["additional_mock_function", "mock_function_one", "funct_new_mock_function", "func_new_mock_function"],
                                           workflows=["additional_mock_workflow", "mock_workflow_one", "wf_new_mock_workflow"])

    # Assert the general structure of the reloaded package
    general_test_package_structure(mock_integration_name, path_package_reloaded)

    # Assert a new components file with 'funct_'  prefix is not created
    expected_component_files = ["funct_additional_mock_function.py"]
    assert not helpers.verify_expected_list(expected_component_files, os.listdir(os.path.join(path_package_reloaded, mock_integration_name, "components")))
    # Assert a new workflow file with 'md_' prefix is not created in data dir
    expected_workflow_files = ["wf_additional_mock_workflow.md"]
    assert not helpers.verify_expected_list(expected_workflow_files, os.listdir(os.path.join(path_package_reloaded, "data")))
    # Assert a new tests file with "funct_" substring is not created
    expected_test_files = ["test_func_additional_mock_function.py"]
    assert not helpers.verify_expected_list(expected_test_files, os.listdir(os.path.join(path_package_reloaded, "tests")))
    # Get new modification time for test workflow file.
    new_wf_modified_time = os.path.getmtime(os.path.join(path_package_reloaded, "data", "wf_mock_workflow_one.md"))
    # Assert modification time of workflow has been updated.
    assert new_wf_modified_time > wf_modified_time


def test_reload_package_w_playbook(fx_copy_fn_main_mock_integration_w_playbooks, fx_get_sub_parser, fx_cmd_line_args_codegen_reload):

    output_path = os.path.join(mock_paths.TEST_TEMP_DIR, "mock_path", "fn_main_mock_integration-1.1.0")
    mock_integration_name = fx_copy_fn_main_mock_integration_w_playbooks[0]
    shutil.move(fx_copy_fn_main_mock_integration_w_playbooks[1], output_path)

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = output_path

    # Add path to a mock export.res file
    sys.argv.extend(["-e", mock_paths.MOCK_RELOAD_EXPORT_RES_W_PLAYBOOK])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    path_package_reloaded = cmd_codegen._reload_package(args)

    import_definition = package_helpers.get_import_definition_from_customize_py(os.path.join(path_package_reloaded, mock_integration_name, package_helpers.PATH_CUSTOMIZE_PY))

    res_objs = sdk_helpers.get_from_export(import_definition,
                                           rules=["Additional Mock Rule", "Mock Manual Rule"],
                                           playbooks=["main_mock_playbook"])

    general_test_package_structure(mock_integration_name, path_package_reloaded)

    assert helpers.verify_expected_list(["Additional Mock Rule", "Mock Manual Rule"], [o.get("x_api_name") for o in res_objs.get("rules")])
    assert helpers.verify_expected_list(["main_mock_playbook"], [o.get("x_api_name") for o in res_objs.get("playbooks")])


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


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_get_results_from_log_file(fx_copy_fn_main_mock_integration, fx_cmd_line_args_codegen_base, fx_get_sub_parser, caplog):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Add arg to gather-results
    sys.argv.extend(["--gather-results", mock_paths.MOCK_APP_LOG_PATH])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen.execute_command(args)

    path_payload_samples = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR)

    # Test output_json_example.json file generated
    output_json_example_contents = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE))
    assert output_json_example_contents.get("version") == 2.1

    # Test output_json_schema.json file generated
    output_json_example_schema = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA))
    output_json_example_schema_props = output_json_example_schema.get("properties")

    assert output_json_example_schema_props.get("version") == {"type": "number"}
    assert output_json_example_schema_props.get("success") == {"type": "boolean"}
    assert output_json_example_schema_props.get("reason") == {}
    assert not output_json_example_schema.get("required")

    # Test WARNING log appears
    assert "WARNING: No results could be found for 'mock_function_two'" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_get_results_from_log_file_specific_function(fx_copy_fn_main_mock_integration, fx_cmd_line_args_codegen_base, fx_get_sub_parser, caplog):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Add arg to gather-results
    sys.argv.extend(["--gather-results", mock_paths.MOCK_APP_LOG_PATH])
    sys.argv.extend(["-f", "mock_function_one", "mock_function_not_exist"])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen.execute_command(args)

    path_payload_samples = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR)

    # Test output_json_example.json file generated
    output_json_example_contents = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE))
    assert output_json_example_contents.get("version") == 2.1

    # Test output_json_schema.json file generated
    output_json_example_schema = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA))
    output_json_example_schema_props = output_json_example_schema.get("properties")

    assert output_json_example_schema_props.get("version") == {"type": "number"}
    assert output_json_example_schema_props.get("success") == {"type": "boolean"}
    assert output_json_example_schema_props.get("reason") == {}
    assert not output_json_example_schema.get("required")

    # Test WARNING log appears
    assert "WARNING: No results could be found for 'mock_function_not_exist'" in caplog.text


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
def test_get_results_from_log_file_no_payload_samples_dir(fx_copy_fn_main_mock_integration, fx_cmd_line_args_codegen_base, fx_get_sub_parser, caplog):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Add arg to gather-results and a path to a mock export.res file for --reload
    sys.argv.extend(["--gather-results", mock_paths.MOCK_APP_LOG_PATH])
    sys.argv.extend(["-e", mock_paths.MOCK_RELOAD_EXPORT_RES])

    path_payload_samples = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR)

    # Remove path_payload_samples
    shutil.rmtree(path_payload_samples)

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen.execute_command(args)

    # Test output_json_example.json file generated
    output_json_example_contents = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE))
    assert output_json_example_contents.get("version") == 2.1

    # Test output_json_schema.json file generated
    output_json_example_schema = sdk_helpers.read_json_file(os.path.join(path_payload_samples, "mock_function_one", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA))
    output_json_example_schema_props = output_json_example_schema.get("properties")
    assert output_json_example_schema_props.get("version") == {"type": "number"}
    assert output_json_example_schema_props.get("reason") == {}

    # Test --reload was ran
    assert "Running 'codegen --reload' to create the default missing files" in caplog.text


def test_gather_results_on_py27(fx_copy_fn_main_mock_integration, fx_cmd_line_args_codegen_base, fx_get_sub_parser):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    # Add arg to gather-results and a path to a mock export.res file for --reload
    sys.argv.extend(["--gather-results", mock_paths.MOCK_APP_LOG_PATH])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]

    if not sdk_helpers.is_python_min_supported_version():

        with pytest.raises(SDKException, match=constants.ERROR_WRONG_PYTHON_VERSION):
            cmd_codegen.execute_command(args)

    else:
        cmd_codegen.execute_command(args)


def test_execute_command():
    # TODO
    pass


def test_codegen_poller(fx_get_sub_parser, fx_cmd_line_args_codegen_package, fx_mk_temp_dir):

    output_path = mock_paths.TEST_TEMP_DIR

    # Add paths to an output base and an export.res file
    sys.argv.extend(["-o", output_path])
    sys.argv.extend(["-e", mock_paths.MOCK_EXPORT_RES])

    # Add arg to gather-results and a path to a mock export.res file for --reload
    sys.argv.extend(["--poller"])

    cmd_codegen = CmdCodegen(fx_get_sub_parser)
    args = cmd_codegen.parser.parse_known_args()[0]
    cmd_codegen._gen_package(args)

    package_name = args.package
    package_path = os.path.join(output_path, args.package)


    general_test_package_structure(package_name, package_path, poller=True)