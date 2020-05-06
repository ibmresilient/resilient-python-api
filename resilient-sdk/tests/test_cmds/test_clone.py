#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import sys
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers as sdk_helpers
from tests.shared_mock_data import mock_data, mock_paths
from resilient_sdk.cmds import base_cmd, CmdClone
from resilient_sdk.cmds.clone import replace_common_object_attrs, replace_workflow_object_attrs, replace_rule_object_attrs, replace_md_object_attrs, replace_function_object_attrs
import uuid
from resilient_sdk.app import get_main_app_parser
from collections import UserDict
from argparse import Namespace
from resilient_sdk.util.resilient_objects import ResilientObjMap

TEST_OBJ= {
    "uuid": uuid.uuid4(),
    "export_key": "TEST_OBJ",
    "name": "My test Obj"
}

from ..helpers import read_mock_json
TEST_EXPORT = read_mock_json("export.JSON")
def test_cmd_docgen_setup(fx_get_sub_parser, fx_cmd_line_args_docgen):
    cmd_docgen = CmdClone(fx_get_sub_parser)

    assert isinstance(cmd_docgen, base_cmd.BaseCmd)
    assert cmd_docgen.CMD_NAME == "clone"
    assert cmd_docgen.CMD_HELP == "Duplicate an existing Action related object (Workflow, Function) with a new api name"
    assert cmd_docgen.CMD_USAGE == """
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
    $ resilient-sdk clone -f <function_to_be_cloned> <new_function_name>"""
    assert cmd_docgen.CMD_DESCRIPTION == "Duplicate an existing Action related object (Workflow, Function) with a new api name"

def test_clone_function(fx_get_sub_parser):
    """test_clone_function test to verify the functionality of test_clone_function
    The _clone_function performs these 3 high level steps :
    1: Validate only 2 names are provided OR that prefix is provided
    2: Validate the source function exists and the target function name will not cause a duplicate
    3: Perform the clone with replace_function_object_attrs
    """
    old_name = "mock_function_one"
    new_name = "new_mocked_func"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)

    export_data = cmd_clone._clone_function(Namespace(function=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Function", new_name,
                                                   old_name, TEST_EXPORT.get("functions").copy())

    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.FUNCTIONS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.FUNCTIONS] != original_obj[ResilientObjMap.FUNCTIONS], "Expected that the export_key was updated"


def test_clone_workflow(fx_get_sub_parser):
    old_name = "mock_workflow_two"
    new_name = "new_mocked_workflow"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
        
    export_data = cmd_clone._clone_workflow(Namespace(workflow=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Workflow", new_name,
                                                   old_name, TEST_EXPORT.get("workflows").copy())

    print(export_data[0])
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.WORKFLOWS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.WORKFLOWS] != original_obj[ResilientObjMap.WORKFLOWS], "Expected that the export_key was updated"

def test_clone_rule(fx_get_sub_parser):
    old_name = "Cyber: Criminal evidence preservation"
    new_name = "Copy: Preserve the evidence"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
        
    export_data = cmd_clone._clone_rule(Namespace(rule=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Rule", new_name,
                                                              old_name, TEST_EXPORT.get("actions").copy())
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.RULES] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.RULES] != original_obj[ResilientObjMap.RULES], "Expected that the export_key was updated"

def test_clone_md(fx_get_sub_parser):
    old_name = "fn_main_mock_integration"
    new_name = "fn_copied_mock_integration"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
        
    export_data = cmd_clone._clone_message_destination(Namespace(messagedestination=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Message Destination", new_name,
                                                              old_name, TEST_EXPORT.get("message_destinations").copy())
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.MESSAGE_DESTINATIONS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.MESSAGE_DESTINATIONS] != original_obj[ResilientObjMap.RULES], "Expected that the export_key was updated"

def test_replace_function_object_attrs():
    # Get the first workflow from the list 
    obj_to_modify = TEST_EXPORT.get("functions")[0].copy()


    old_function_name = obj_to_modify[ResilientObjMap.FUNCTIONS]
    new_obj =obj_to_modify.copy()
    new_obj = replace_function_object_attrs(obj_to_modify, "test_new_function")

    assert new_obj[ResilientObjMap.FUNCTIONS] != old_function_name

def test_replace_workflow_object_attrs():
    # Get the first workflow from the list 
    obj_to_modify = TEST_EXPORT.get("workflows")[0].copy()


    old_workflow_name = obj_to_modify[ResilientObjMap.WORKFLOWS]
    new_obj =obj_to_modify.copy()
    new_obj = replace_workflow_object_attrs(obj_to_modify, obj_to_modify[ResilientObjMap.WORKFLOWS], "test_new_workflow", obj_to_modify['name'])

    assert new_obj[ResilientObjMap.WORKFLOWS] != old_workflow_name

def test_replace_rule_object_attrs():
    # Get the first rule from the list 
    obj_to_modify = TEST_EXPORT.get("actions")[0].copy()


    old_rule_name = obj_to_modify[ResilientObjMap.RULES]
    new_obj =obj_to_modify.copy()
    new_obj = replace_rule_object_attrs(obj_to_modify, "test_new_rule")

    assert new_obj[ResilientObjMap.RULES] != old_rule_name

def test_replace_md_object_attrs():
    # Get the first rule from the list 
    obj_to_modify = TEST_EXPORT.get("message_destinations")[0].copy()


    old_md_name = obj_to_modify[ResilientObjMap.MESSAGE_DESTINATIONS]
    new_obj =obj_to_modify.copy()
    new_obj = replace_md_object_attrs(obj_to_modify, "fn_msg_dst")

    assert new_obj[ResilientObjMap.RULES] != old_md_name

def test_replace_common_object_attrs(fx_get_sub_parser):
    test_name = "My new name"
    cmd_clone = CmdClone(fx_get_sub_parser)
    new_object = replace_common_object_attrs(TEST_OBJ, test_name)
    assert new_object['name'] == test_name, "Expected name to be updated"

def test_action_obj_was_specified():
    pass