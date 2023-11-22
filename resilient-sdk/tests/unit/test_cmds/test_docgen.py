#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import os
import sys

from packaging.version import parse as parse_version
from resilient_sdk.cmds import CmdDocgen, base_cmd
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from tests.shared_mock_data import mock_paths


def test_cmd_docgen_setup(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)

    assert isinstance(cmd_docgen, base_cmd.BaseCmd)
    assert cmd_docgen.CMD_NAME == "docgen"
    assert cmd_docgen.CMD_HELP == "Generates boilerplate documentation for an app."
    assert cmd_docgen.CMD_USAGE == """
    $ resilient-sdk docgen -p <path_to_package>
    $ resilient-sdk docgen -p <name_of_package> --settings <path_to_custom_sdk_settings_file>
    $ resilient-sdk docgen -p <name_of_package> --poller # for a poller app
    $ resilient-sdk docgen -e export.res
    $ resilient-sdk docgen -e playbook1.resz playbook2.resz -o /path/to/save/playbooks_readme.md
    $ resilient-sdk docgen -e . -o README.md # reads all exports in current directory and outputs to README.md"""
    assert cmd_docgen.CMD_DESCRIPTION == cmd_docgen.CMD_HELP

    args = cmd_docgen.parser.parse_known_args()[0]
    assert args.package == "fn_main_mock_integration"


def test_get_fn_input_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, functions=["mock_function_two"])

    fn = import_def_data.get("functions")[0]
    fn_inputs = CmdDocgen._get_fn_input_details(fn)

    fn_input = next(x for x in fn_inputs if x["api_name"] == "mock_input_number")
    mock_input = {'api_name': u'mock_input_number', 'name': u'mock_input_number', 'type': 'number', 'required': 'Yes', 'placeholder': u'-', 'tooltip': u'a mock tooltip  ล ฦ ว ศ ษ ส ห ฬ อ'}

    assert fn_input == mock_input


def test_get_fn_input_details_defaults():
    mock_function = {
        "inputs": [
            {"api_name": "", "placeholder": "", "tooltip": ""}
        ]
    }

    fn_input = CmdDocgen._get_fn_input_details(mock_function)[0]
    mock_input = {'api_name': None, 'name': None, 'type': None, 'required': u'No', 'placeholder': u'-', 'tooltip': u'-'}

    assert fn_input == mock_input


def test_get_function_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition,
                                                  functions=["mock_function_two"],
                                                  workflows=["mock_workflow_two"])

    function_details = CmdDocgen._get_function_details(import_def_data)
    the_function = function_details[0]

    assert the_function.get("name") == u"mock function  ล ฦ ว ศ ษ ส ห ฬ อ two"
    assert the_function.get("pre_processing_script") in u"""# mock pre script of function  ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ two:\n\ninputs.mock_input_boolean = False\ninputs.mock_input_number = 1001\ninputs.mock_input_text = u" ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ ramdom text" """
    assert the_function.get("post_processing_script") is None

def test_get_function_details_w_playbook():
    constants.CURRENT_SOAR_SERVER_VERSION = parse_version("46.0") # setting SOAR server version to 46.0

    import_definition = package_helpers.get_import_definition_from_local_export_res(mock_paths.MOCK_EXPORT_RES_W_PLAYBOOK_W_SCRIPTS)

    import_def_data = sdk_helpers.get_from_export(import_definition,
                                                  functions=["fn_test_dynamic_input"],
                                                  playbooks=["fn_test_dynamic_input"],
                                                  scripts=["handle output for playbook readme"])

    function_details = CmdDocgen._get_function_details(import_def_data)
    the_function = function_details[0]

    assert the_function.get("name") == u"fn_test_dynamic_input"
    assert the_function.get("pre_processing_script") == '"""pre script\n"""' 
    assert the_function.get("post_processing_script") == u"""a_variable = \"a string\"\nb_variable = \"b string\"\nc_variable = 12345\n# d_variable = playbook.functions.results.output\nd_variable = playbook.functions.results.output2\no = \"output\""""

    constants.CURRENT_SOAR_SERVER_VERSION = None # setting SOAR server version to 46.0

def test_get_script_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, scripts=["Mock Script One"])
    scripts = import_def_data.get("scripts")
    script_details = CmdDocgen._get_script_details(scripts)
    the_script = script_details[0]

    assert the_script.get("name") == "Mock Script One"
    assert the_script.get("simple_name") == "mock-script-one"
    assert the_script.get("anchor") == "mock-script-one"
    assert the_script.get("description") == "a sample Artifact script"
    assert the_script.get("object_type") == "artifact"
    assert the_script.get("script_text") == """log.info("Print this message")"""


def test_get_rule_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, rules=["Mock: Auto Rule"])

    rule_details = CmdDocgen._get_rule_details(import_def_data.get("rules"))
    the_rule = rule_details[0]

    mock_rule = {'name': u'Mock: Auto Rule', 'object_type': u'incident', 'workflow_triggered': u'mock_workflow_one', 'simple_name': u'mock-auto-rule', 'conditions': u'object_added'}

    assert the_rule == mock_rule

def test_get_playbook_details():
    constants.CURRENT_SOAR_SERVER_VERSION = parse_version("46.0") # setting SOAR server version to 46.0

    import_definition = package_helpers.get_import_definition_from_local_export_res(mock_paths.MOCK_EXPORT_RES_W_PLAYBOOK_W_SCRIPTS)
    import_def_data = sdk_helpers.get_from_export(import_definition, playbooks=["fn_test_dynamic_input"])

    playbook_details = CmdDocgen._get_playbook_details(import_def_data.get("playbooks"))

    assert playbook_details[0]["api_name"] == "fn_test_dynamic_input"
    assert playbook_details[0]["name"] == "fn_test_dynamic_input"
    assert playbook_details[0]["object_type"] == "incident"
    assert playbook_details[0]["status"] == "enabled"
    assert playbook_details[0]["activation_type"] == "Manual"
    assert playbook_details[0]["conditions"] == "incident.addr has_a_value AND incident.creator_id equals admin@example.com"

    constants.CURRENT_SOAR_SERVER_VERSION = None # setting SOAR server version to 46.0


def test_get_datatable_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, datatables=["mock_data_table"])

    datatable_details = CmdDocgen._get_datatable_details(import_def_data.get("datatables"))
    the_datatable = datatable_details[0]

    mock_datatable = {
        'name': u'Mock: Data Table  ล ฦ ว ศ ษ ส ห ฬ อ',
        'anchor': u'mock-data-table--ล-ฦ-ว-ศ-ษ-ส-ห-ฬ-อ',
        'api_name': u'mock_data_table',
        'simple_name': u'mock-data-table----------',
        'columns': [
            {'name': u'mock col one', 'api_name': u'mock_col_one', 'type': u'text', 'tooltip': u'a tooltip  ล ฦ ว ศ ษ ส ห ฬ อ'},
            {'name': u'mock  ล ฦ ว ศ ษ ส ห ฬ อ col two', 'api_name': u'mok_col_two', 'type': u'number', 'tooltip': u'tooltip  ล ฦ ว ศ ษ ส ห ฬ อ'}
        ]
    }

    assert the_datatable == mock_datatable


def test_get_datatable_details_defaults():
    mock_datables = [
        {
            "display_name": "mock_name",
            "name": "mock_name",
            "api_name": "mock_name",
            "fields": {
                "col_one": {}
            }
        }
    ]

    the_datatable = CmdDocgen._get_datatable_details(mock_datables)[0]
    mock_datatable = {'name': 'mock_name', 'anchor': 'mock_name', 'api_name': None, 'simple_name': 'mock-name', 'columns': [{'name': None, 'api_name': None, 'type': None, 'tooltip': '-'}]}

    assert the_datatable == mock_datatable


def test_get_custom_fields_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, fields=["mock_field_number", "mock_field_text_area"])

    field_details = CmdDocgen._get_custom_fields_details(import_def_data.get("fields"))

    field_one = next(x for x in field_details if x["api_name"] == "mock_field_number")
    field_two = next(x for x in field_details if x["api_name"] == "mock_field_text_area")

    mock_field_one = {'api_name': u'mock_field_number', 'label': u'Mock:  ล ฦ ว ศ ษ ส ห ฬ อ field number', 'type': u'number', 'prefix': u'properties', 'placeholder': u'-', 'tooltip': u'a mock tooltip  ล ฦ ว ศ ษ ส ห ฬ อ'}
    mock_field_two = {'api_name': u'mock_field_text_area', 'label': u'Mock: Field Text Area  ล ฦ ว ศ ษ ส ห ฬ อ', 'type': u'textarea', 'prefix': u'properties', 'placeholder': u'-', 'tooltip': u'a tooltip  ล ฦ ว ศ ษ ส ห ฬ อ'}

    assert field_one == mock_field_one
    assert field_two == mock_field_two


def test_get_custom_fields_details_defaults():
    mock_fields = [
        {
            "api_name": "mock_field",
            "placeholder": "",
            "tooltip": ""
        }
    ]

    field_details = CmdDocgen._get_custom_fields_details(mock_fields)[0]
    mock_field = {'placeholder': '-', 'tooltip': '-', 'prefix': None, 'api_name': None, 'label': None, 'type': None}

    assert field_details == mock_field


def test_get_custom_artifact_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, artifact_types=["mock_artifact_2"])

    artifact_details = CmdDocgen._get_custom_artifact_details(import_def_data.get("artifact_types"))
    the_artifact = artifact_details[0]

    mock_artifact = {
        'api_name': u'mock_artifact_2',
        'display_name': u'Mock Artifact 2 ㌎ ㌏ ㌐ ㌑ ㌒ ㌓ ㌔ ㌕ ㌖',
        'description': u'㌎ ㌏ ㌐ ㌑ ㌒ ㌓ ㌔ ㌕ ㌖ ㌎ ㌏ ㌐ ㌑ ㌒ ㌓ ㌔ ㌕ ㌖asdf ㌎ ㌏ ㌐ ㌑ ㌒ ㌓ ㌔ ㌕ ㌖'
    }

    assert the_artifact == mock_artifact

def test_get_poller_details(fx_copy_fn_main_mock_integration):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    poller_templates = CmdDocgen._get_poller_details(path_fn_main_mock_integration, mock_integration_name)

    assert len(poller_templates) == 3
    assert package_helpers.BASE_NAME_POLLER_CREATE_CASE_TEMPLATE in poller_templates
    assert package_helpers.BASE_NAME_POLLER_UPDATE_CASE_TEMPLATE in poller_templates
    assert package_helpers.BASE_NAME_POLLER_CLOSE_CASE_TEMPLATE in poller_templates


def test_app_log_results_are_used(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_docgen):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration

    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]
    cmd_docgen.execute_command(args)

    readme_file = sdk_helpers.read_file(os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_README))

    assert '  "custom_results": "these are my custom results!"' in "\n".join(readme_file)

def test_sdk_settings_for_docgen(fx_copy_fn_main_mock_integration, fx_get_sub_parser, fx_cmd_line_args_docgen):

    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # Replace cmd line arg "fn_main_mock_integration" with path to temp dir location
    sys.argv[sys.argv.index(mock_integration_name)] = path_fn_main_mock_integration
    # Add cmd line arg
    sys.argv.extend(["--settings", mock_paths.MOCK_SDK_SETTINGS_PATH])

    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]
    cmd_docgen.execute_command(args)

    readme_file = sdk_helpers.read_file(os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_README))

    assert "This is an IBM supported app" in "\n".join(readme_file)

def test_get_export_paths_from_args(fx_copy_fn_main_mock_integration, caplog):
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]

    # find all files in fn_main_mock_integration, and manually add README.md (which will be found)
    # just by virtue of being in the directory. we ensure that it isn't counted twice
    export_files = CmdDocgen._get_export_paths_from_args([path_fn_main_mock_integration, os.path.join(path_fn_main_mock_integration, "README.md"), "doesntexist.resz"])

    assert len(export_files) == 7
    assert export_files == CmdDocgen._get_export_paths_from_args([path_fn_main_mock_integration])
    assert "Skipping --export arg" in caplog.text

def test_add_payload_samples_to_functions(fx_copy_fn_main_mock_integration):
    mock_integration_name = fx_copy_fn_main_mock_integration[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration[1]
    path_customize_py_file = os.path.join(path_fn_main_mock_integration, mock_integration_name, "util", "customize.py")
    path_payload_samples = os.path.join(path_fn_main_mock_integration, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR)

    import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py_file)
    import_def_data = sdk_helpers.get_from_export(import_definition,
                                                  functions=["mock_function_one"],
                                                  workflows=["mock_workflow_one"])

    function_details = CmdDocgen._get_function_details(import_def_data)
    assert "results" not in function_details[0]
    CmdDocgen._add_payload_samples_to_functions(function_details, path_payload_samples)

    assert "results" in function_details[0]
    assert function_details[0]["results"]["custom_results"] == "these are my custom results!"

def test_get_all_objects_for_jinja_render(fx_get_sub_parser, fx_copy_fn_main_mock_integration_w_playbooks):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    mock_integration_name = fx_copy_fn_main_mock_integration_w_playbooks[0]
    path_fn_main_mock_integration = fx_copy_fn_main_mock_integration_w_playbooks[1]
    path_customize_py_file = os.path.join(path_fn_main_mock_integration, mock_integration_name, "util", "customize.py")

    export_contents = package_helpers.get_import_definition_from_customize_py(path_customize_py_file)

    results = cmd_docgen._get_all_objects_for_jinja_render(export_contents)

    assert len(results[0]) == 4 # 4 functions
    assert len(results[1]) == 3 # 3 scripts
    assert len(results[2]) == 19 # 19 rules
    assert len(results[3]) == 1 # 1 datatable
    assert len(results[4]) == 79 # 79 custom fields
    assert len(results[5]) == 42 # 42 artifacts
    assert len(results[6]) == 1 # 1 playbook

def test_get_app_package_docgen_details(fx_get_sub_parser, fx_cmd_line_args_docgen, fx_copy_fn_main_mock_integration_w_playbooks):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    fx_cmd_line_args_docgen[-1] = fx_copy_fn_main_mock_integration_w_playbooks[1]
    package_details = cmd_docgen._get_app_package_docgen_details(cmd_docgen.parser.parse_known_args()[0])

    assert package_details[0] == "fn_main_mock_integration"
    assert len(package_details[1]["workflows"]) == 2
    assert "/payload_samples" in package_details[2]
    assert "/README.md" in package_details[3]
    assert all(req in package_details[4] for req in ("setup_py_attributes", "res_circuits_dep_str", "jinja_app_configs", "supported_app", "poller_templates"))

def test_get_export_docgen_details_res_file(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    path_export = mock_paths.MOCK_EXPORT_RES
    export_details = cmd_docgen._get_export_docgen_details(path_export)

    assert export_details[0] == "mock_export"
    assert len(export_details[1]["workflows"]) == 2
    assert os.path.basename(export_details[2]) == "README.md"

def test_get_export_docgen_details_res_file_custom_output_path(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    path_export = mock_paths.MOCK_EXPORT_RES
    export_details = cmd_docgen._get_export_docgen_details(path_export, output_path="export.md")

    assert export_details[0] == "mock_export"
    assert len(export_details[1]["workflows"]) == 2
    assert os.path.basename(export_details[2]) == "export.md"

def test_get_export_docgen_details_res_zip_file(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    path_export = mock_paths.MOCK_EXPORT_RESZ
    export_details = cmd_docgen._get_export_docgen_details(path_export)

    assert export_details[0] == "mock_export"
    assert len(export_details[1]["workflows"]) == 2
    assert os.path.basename(export_details[2]) == "README.md"


def test_execute_command_for_app_package(fx_get_sub_parser, fx_cmd_line_args_docgen, fx_copy_fn_main_mock_integration_w_playbooks, caplog):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    fx_cmd_line_args_docgen[-1] = fx_copy_fn_main_mock_integration_w_playbooks[1]

    cmd_docgen.execute_command(cmd_docgen.parser.parse_known_args()[0])

    assert "Rendering README for" in caplog.text
    assert "Writing README to: {}/README.md".format(fx_copy_fn_main_mock_integration_w_playbooks[1]) in caplog.text

def test_execute_command_for_export(fx_get_sub_parser, fx_cmd_line_args_docgen_export_file, caplog):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)

    cmd_docgen.execute_command(cmd_docgen.parser.parse_known_args()[0])

    assert "Rendering README for" in caplog.text
    assert "mock_xml_test_report.xml' was skipped for 'docgen --export' because it was not in the proper" in caplog.text
    assert "Writing README to" in caplog.text
