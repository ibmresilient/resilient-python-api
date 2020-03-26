#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import sys
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from tests.shared_mock_data import mock_paths
from resilient_sdk.cmds import base_cmd, CmdDocgen


def test_cmd_docgen_setup(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdDocgen(fx_get_sub_parser)

    assert isinstance(cmd_docgen, base_cmd.BaseCmd)
    assert cmd_docgen.CMD_NAME == "docgen"
    assert cmd_docgen.CMD_HELP == "Generate documentation for an app"
    assert cmd_docgen.CMD_USAGE == """
    $ resilient-sdk docgen -p <path_to_package>
    $ resilient-sdk docgen -p <path_to_package> --user-guide
    $ resilient-sdk docgen -p <path_to_package> --install-guide"""
    assert cmd_docgen.CMD_DESCRIPTION == "Generate documentation for an app"

    args = cmd_docgen.parser.parse_known_args()[0]
    assert args.p == "fn_main_mock_integration"
    assert args.install_guide is False
    assert args.user_guide is False


def test_only_install_guide_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--install-guide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.install_guide is True
    assert args.user_guide is False


def test_only_iguide_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--iguide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.install_guide is True
    assert args.user_guide is False


def test_only_install_user_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--user-guide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.install_guide is False
    assert args.user_guide is True


def test_only_uguide_arg(fx_get_sub_parser, fx_cmd_line_args_docgen):
    sys.argv.append("--uguide")
    cmd_docgen = CmdDocgen(fx_get_sub_parser)
    args = cmd_docgen.parser.parse_known_args()[0]

    assert args.p == "fn_main_mock_integration"
    assert args.install_guide is False
    assert args.user_guide is True


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

    functions = import_def_data.get("functions")
    workflows = import_def_data.get("workflows")

    function_details = CmdDocgen._get_function_details(functions, workflows)
    the_function = function_details[0]

    assert the_function.get("name") == u"mock function  ล ฦ ว ศ ษ ส ห ฬ อ two"
    assert the_function.get("pre_processing_script") in u"""# mock pre script of function  ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ two:\n\ninputs.mock_input_boolean = False\ninputs.mock_input_number = 1001\ninputs.mock_input_text = u" ล ฦ ว ศ ษ ส ห ฬ อ ล ฦ ว ศ ษ ส ห ฬ อ ramdom text" """
    assert the_function.get("post_processing_script") is None


def test_get_rule_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, rules=["Mock: Auto Rule"])

    rule_details = CmdDocgen._get_rule_details(import_def_data.get("rules"))
    the_rule = rule_details[0]

    mock_rule = {'name': u'Mock: Auto Rule', 'object_type': u'incident', 'workflow_triggered': u'mock_workflow_one'}

    assert the_rule == mock_rule


def test_get_datatable_details():
    import_definition = package_helpers.get_import_definition_from_customize_py(mock_paths.MOCK_CUSTOMIZE_PY)
    import_def_data = sdk_helpers.get_from_export(import_definition, datatables=["mock_data_table"])

    datatable_details = CmdDocgen._get_datatable_details(import_def_data.get("datatables"))
    the_datatable = datatable_details[0]

    mock_datatable = {
        'name': u'Mock: Data Table  ล ฦ ว ศ ษ ส ห ฬ อ',
        'anchor': u'mock-data-table----------',
        'api_name': u'mock_data_table',
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
    mock_datatable = {'name': 'mock_name', 'anchor': 'mock-name', 'api_name': None, 'columns': [{'name': None, 'api_name': None, 'type': None, 'tooltip': '-'}]}

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


def test_execute_command():
    # TODO
    pass