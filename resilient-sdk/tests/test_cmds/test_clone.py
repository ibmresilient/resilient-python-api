#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import uuid
from argparse import Namespace
import copy
from resilient_sdk.cmds import base_cmd, CmdClone
from resilient_sdk.cmds.clone import replace_common_object_attrs, replace_workflow_object_attrs, replace_rule_object_attrs, replace_md_object_attrs, replace_function_object_attrs
from resilient_sdk.util.resilient_objects import ResilientObjMap
from ..helpers import read_mock_json

TEST_OBJ = {
    "uuid": uuid.uuid4(),
    "export_key": "TEST_OBJ",
    "name": "My test Obj"
}

TEST_EXPORT = read_mock_json("export.JSON")


def test_cmd_docgen_setup(fx_get_sub_parser):
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

    export_data = cmd_clone._clone_function(
        Namespace(function=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Function", new_name,
                                                           old_name, copy.copy(TEST_EXPORT.get("functions")))

    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.FUNCTIONS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.FUNCTIONS] != original_obj[
        ResilientObjMap.FUNCTIONS], "Expected that the export_key was updated"


def test_clone_workflow(fx_get_sub_parser):
    """test_clone_workflow test which verifies a known named workflow can be cloned with a new name
    _clone_workflow performs these 3 high level steps :
    1: Validate only 2 names are provided OR that prefix is provided
    2: Validate the source object exists and the target object name will not cause a duplicate
    3: Perform the clone
    :param fx_get_sub_parser: a fixture mocking the functionality of a argparse subparser
    :type fx_get_sub_parser: fixture
    """
    old_name = "mock_workflow_two"
    new_name = "new_mocked_workflow"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)

    export_data = cmd_clone._clone_workflow(
        Namespace(workflow=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Workflow", new_name,
                                                           old_name, copy.copy(TEST_EXPORT.get("workflows")))
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.WORKFLOWS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.WORKFLOWS] != original_obj[
        ResilientObjMap.WORKFLOWS], "Expected that the export_key was updated"


def test_clone_rule(fx_get_sub_parser):
    """test_clone_rule test which verifies a known named rule can be cloned with a new name

    _clone_rule performs these 3 high level steps :
    1: Validate only 2 names are provided OR that prefix is provided
    2: Validate the source object exists and the target object name will not cause a duplicate
    3: Perform the clone
    :param fx_get_sub_parser: a fixture mocking the functionality of a argparse subparser
    :type fx_get_sub_parser: fixture
    """
    old_name = "Cyber: Criminal evidence preservation"
    new_name = "Copy: Preserve the evidence"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)

    export_data = cmd_clone._clone_rule(
        Namespace(rule=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Rule", new_name,
                                                           old_name, copy.copy(TEST_EXPORT.get("actions")))
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.RULES] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.RULES] != original_obj[ResilientObjMap.RULES], "Expected that the export_key was updated"


def test_clone_md(fx_get_sub_parser):
    """test_clone_md test which attempts to find and clone a named message destination in the export.json

    _clone_md performs these 3 high level steps :
    1: Validate only 2 names are provided OR that prefix is provided
    2: Validate the source object exists and the target object name will not cause a duplicate
    3: Perform the clone
    :param fx_get_sub_parser: a fixture mocking the functionality of a argparse subparser
    :type fx_get_sub_parser: fixture
    """
    old_name = "fn_main_mock_integration"
    new_name = "fn_copied_mock_integration"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)

    export_data = cmd_clone._clone_message_destination(
        Namespace(messagedestination=[old_name, new_name]), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names("Message Destination", new_name,
                                                           old_name, copy.copy(TEST_EXPORT.get("message_destinations")))
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.MESSAGE_DESTINATIONS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.MESSAGE_DESTINATIONS] != original_obj[
        ResilientObjMap.RULES], "Expected that the export_key was updated"


def test_replace_function_object_attrs():
    """test_replace_function_object_attrs test to verify the functionality of replacing a workflows unique attributes

    :param obj_to_modify: the object to be modified, in this case a function
    :type obj_to_modify: dict
    :param new_obj_api_name: the name of the function to modify
    :type new_obj_api_name: str
    :return: the modified object
    :rtype: dict
    """
    # Get the first workflow from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("functions")[0])

    old_function_name = obj_to_modify[ResilientObjMap.FUNCTIONS]
    new_obj = copy.copy(obj_to_modify)
    new_obj = replace_function_object_attrs(obj_to_modify, "test_new_function")

    assert new_obj[ResilientObjMap.FUNCTIONS] != old_function_name


def test_replace_workflow_object_attrs():
    """test_replace_workflow_object_attrs test to verify the functionality of replacing a workflows unique attributes
    """
    # Get the first workflow from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("workflows")[0])

    old_workflow_name = obj_to_modify[ResilientObjMap.WORKFLOWS]
    new_obj = copy.copy(obj_to_modify)
    new_obj = replace_workflow_object_attrs(
        obj_to_modify, obj_to_modify[ResilientObjMap.WORKFLOWS], "test_new_workflow", obj_to_modify['name'])

    assert new_obj[ResilientObjMap.WORKFLOWS] != old_workflow_name


def test_replace_rule_object_attrs():
    """test_replace_rule_object_attrs test to verify the functionality of replacing a rules unique attributes
    """
    # Get the first rule from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("actions")[0])

    old_rule_name = obj_to_modify[ResilientObjMap.RULES]
    new_obj = copy.copy(obj_to_modify)
    new_obj = replace_rule_object_attrs(obj_to_modify, "test_new_rule")

    assert new_obj[ResilientObjMap.RULES] != old_rule_name


def test_replace_md_object_attrs():
    """test_replace_md_object_attrs test to verify the functionality of replacing a message destinations unique attributes
    """
    # Get the first rule from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("message_destinations")[0])

    old_md_name = obj_to_modify[ResilientObjMap.MESSAGE_DESTINATIONS]
    new_obj = copy.copy(obj_to_modify)
    new_obj = replace_md_object_attrs(obj_to_modify, "fn_msg_dst")

    assert new_obj[ResilientObjMap.RULES] != old_md_name


def test_replace_common_object_attrs():
    """test_replace_common_object_attrs test to verify the functionality of replacing an action objects unique attributes

    :param fx_get_sub_parser: [description]
    :type fx_get_sub_parser: [type]
    """
    test_name = "My new name"
    original_uuid = TEST_OBJ['uuid']
    original_export_key = TEST_OBJ['export_key']
    new_object = replace_common_object_attrs(TEST_OBJ, test_name)
    assert new_object['name'] == test_name, "Expected name to be updated"
    assert new_object['uuid'] != original_uuid, "Expected uuid to be updated"
    assert new_object['export_key'] != original_export_key, "Expected export_key to be updated"


def test_action_obj_was_specified():
    pass
