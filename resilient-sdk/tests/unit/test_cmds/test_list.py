#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

import sys

import pytest
from resilient_sdk.cmds import CmdList, base_cmd
from resilient_sdk.cmds.list import TAB_SEP


def test_cmd_list_init(fx_get_sub_parser):
    cmd_list = CmdList(fx_get_sub_parser)

    assert isinstance(cmd_list, base_cmd.BaseCmd)
    assert cmd_list.CMD_NAME == "list"
    assert cmd_list.CMD_HELP == "Lists available objects from SOAR."
    assert cmd_list.CMD_DESCRIPTION == "List available objects from SOAR. For each of the objects below, either leave blank to list all, provide a prefix string to filter by prefix, or provide a regex to filter matching object names."
    assert cmd_list.CMD_USAGE == """
    $ resilient-sdk list --function                           # list all functions
    $ resilient-sdk list --function "fn_my_app.*" --playbook  # list all functions that start with fn_my_app and all playbooks
    $ resilient-sdk list --global-filter ".*(?i)cyber.*"      # matches all objects with "cyber" in them (uses '(?i)' for case-insensitive)
    $ resilient-sdk list --function --codegen-format          # list all functions and give output in codegen format
    """

def test_cmd_list_list_objects_functions_no_filters(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-f"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)

    assert "Functions:" in caplog.text
    assert "{0}- mock_function_one".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function_two".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function__three".format(TAB_SEP) in caplog.text

def test_cmd_list_list_objects_functions_with_filter(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-f", r"do not find", r"another do not find"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)

    assert "No Functions matching filter 'do not find' or 'another do not find' in this export" in caplog.text

def test_cmd_list_list_objects_datatables_no_filters(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-d"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)

    assert "Datatables:" in caplog.text
    assert "{0}- mock_data_table".format(TAB_SEP) in caplog.text

def test_cmd_list_list_objects_datatables_with_filter(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-d", r"my_dt.*"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)

    assert "No Datatables matching filter 'my_dt.*' in this export" in caplog.text

def test_cmd_list_list_objects_global(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-g", r".*mock.*"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)


    assert "Functions:" in caplog.text
    assert "{0}- a_mock_function_with_no_unicode_characters_in_name".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function__three".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function_one".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function_two".format(TAB_SEP) in caplog.text
    assert "Message Destinations:" in caplog.text
    assert "{0}- fn_main_mock_integration".format(TAB_SEP) in caplog.text
    assert "Playbooks:" in caplog.text
    assert "{0}- main_mock_playbook".format(TAB_SEP) in caplog.text
    assert "Artifact Types:" in caplog.text
    assert "{0}- mock_artifact_2".format(TAB_SEP) in caplog.text
    assert "{0}- mock_artifact_type_one".format(TAB_SEP) in caplog.text
    assert "Tasks:" in caplog.text
    assert "{0}- mock_cusom_task__________two".format(TAB_SEP) in caplog.text
    assert "{0}- mock_custom_task_one".format(TAB_SEP) in caplog.text
    assert "Datatables:" in caplog.text
    assert "{0}- mock_data_table".format(TAB_SEP) in caplog.text
    assert "Incident Fields:" in caplog.text
    assert "{0}- mock_field_text_area".format(TAB_SEP) in caplog.text
    assert "{0}- mock_field_text".format(TAB_SEP) in caplog.text
    assert "{0}- mock_field_number".format(TAB_SEP) in caplog.text
    assert "Workflows:" in caplog.text
    assert "{0}- mock_workflow_one".format(TAB_SEP) in caplog.text
    assert "{0}- mock_workflow_two".format(TAB_SEP) in caplog.text

def test_cmd_list_list_objects_global_override_fields_filter(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    sys.argv.extend(["-g", r".*mock.*", "-fd", "mock.*number.*"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)


    assert "Functions:" in caplog.text
    assert "{0}- a_mock_function_with_no_unicode_characters_in_name".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function__three".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function_one".format(TAB_SEP) in caplog.text
    assert "{0}- mock_function_two".format(TAB_SEP) in caplog.text
    assert "Message Destinations:" in caplog.text
    assert "{0}- fn_main_mock_integration".format(TAB_SEP) in caplog.text
    assert "Playbooks:" in caplog.text
    assert "{0}- main_mock_playbook".format(TAB_SEP) in caplog.text
    assert "Artifact Types:" in caplog.text
    assert "{0}- mock_artifact_2".format(TAB_SEP) in caplog.text
    assert "{0}- mock_artifact_type_one".format(TAB_SEP) in caplog.text
    assert "Tasks:" in caplog.text
    assert "{0}- mock_cusom_task__________two".format(TAB_SEP) in caplog.text
    assert "{0}- mock_custom_task_one".format(TAB_SEP) in caplog.text
    assert "Datatables:" in caplog.text
    assert "{0}- mock_data_table".format(TAB_SEP) in caplog.text
    assert "Incident Fields:" in caplog.text
    assert "{0}- mock_field_number".format(TAB_SEP) in caplog.text
    assert "Workflows:" in caplog.text
    assert "{0}- mock_workflow_one".format(TAB_SEP) in caplog.text
    assert "{0}- mock_workflow_two".format(TAB_SEP) in caplog.text

    # compared with the test above, these are now not present because the
    # function filter we used superseded the global filter and filtered these out
    assert "{0}- mock_field_text_area".format(TAB_SEP) not in caplog.text
    assert "{0}- mock_field_text".format(TAB_SEP) not in caplog.text


def test_cmd_list_list_codegen_format_include_md_func_dt(fx_get_sub_parser, fx_cmd_line_args_list, caplog):
    # also include playbooks with an impossible regex and note that --playbook isn't in the output
    sys.argv.extend(["-d", "-m", "-f", r"mock_.*", "-pb", r"impossible_regex_wont_find_any Playbooks", "-cf"])
    cmd_list = CmdList(fx_get_sub_parser)
    args = cmd_list.parser.parse_known_args()[0]
    cmd_list.execute_command(args)

    assert "resilient-sdk codegen" in caplog.text
    assert "--messagedestination fn_main_mock_integration fn_test_two" in caplog.text
    assert "--function mock_function__three mock_function_one mock_function_two" in caplog.text
    assert "--datatable mock_data_table" in caplog.text
    assert "--playbook" not in caplog.text
    assert "a_mock_function_with_no_unicode_characters_in_name" not in caplog.text

@pytest.mark.parametrize("names_list, filters, expected_output", [
    (
        ["fn_1", "fn_2", "func_3"],
        [r"fn.*\d$"],
        ["fn_1", "fn_2"]
    ),
    (
        ["fn_1", "fn_two", "fn_3"],
        [r"fn.*\d$"],
        ["fn_1", "fn_3"]
    ),
    (
        ["darktrace_field_1", "darktrace_field_2", "fn_darktrace", "fn_aws_field_1"],
        [r"darktrace"], # can provide just a prefix (note 'fn_darktrace' is skipped here because not prefix)
        ["darktrace_field_1", "darktrace_field_2"]
    ),
    (
        ["darktrace_field_1", "darktrace_field_2", "fn_aws_field_1"],
        [r".*field.*"],
        ["darktrace_field_1", "darktrace_field_2", "fn_aws_field_1"]
    ),
    (
        ["fn_1", "fn_2", "func_3"],
        [r".*\d$"],
        ["fn_1", "fn_2", "func_3"]
    ),
    (
        ["fn_1", "fn_2", "func_3"],
        [r".*"],
        ["fn_1", "fn_2", "func_3"]
    ),
    (
        ["Cyber", "cyber", "cybersecurity", "func_cybersecurity"],
        [r"(?i)cyber"], # ignore case, prefix-style match
        ["Cyber", "cyber", "cybersecurity"]
    )
])
def test_cmd_list_apply_regex_filters(names_list, filters, expected_output):
    assert CmdList._apply_regex_filters(names_list, filters) == expected_output
