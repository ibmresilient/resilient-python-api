#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import uuid
from argparse import Namespace
import copy
from resilient_sdk.cmds import base_cmd, CmdClone
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util.sdk_exception import SDKException

from ..helpers import read_mock_json
import pytest
TEST_OBJ = {
    "uuid": uuid.uuid4(),
    "export_key": "TEST_OBJ",
    "name": "My test Obj"
}

TEST_EXPORT = read_mock_json("export.JSON")
# Mandatory keys for a configuration import
MANDATORY_KEYS = ["incident_types", "fields"]
# Map from export object keys to each objects unique identifier
EXPORT_TYPE_MAP = {'actions': ResilientObjMap.RULES,
                   'functions': ResilientObjMap.FUNCTIONS, 'workflows': ResilientObjMap.WORKFLOWS}
TEST_CLONE_FAILURE_DATA = [(("bad_function", "new_func"), "Function", ResilientObjMap.FUNCTIONS, 'functions', CmdClone.replace_function_object_attrs),
                           (("bad_rule", "new_rule"), "Rule", ResilientObjMap.RULES,
                            'actions', CmdClone.replace_rule_object_attrs),
                           (("bad_md", "new_md"), "Message Destination", ResilientObjMap.MESSAGE_DESTINATIONS,
                            'message_destinations', CmdClone.replace_md_object_attrs),
                           (("bad_script", "new_script"), "Script", ResilientObjMap.SCRIPTS, 'scripts', CmdClone.replace_function_object_attrs)]


def test_cmd_clone_setup(fx_get_sub_parser):
    """
    Test to verify the cli information from the clone command
    """
    cmd_clone = CmdClone(fx_get_sub_parser)

    assert isinstance(cmd_clone, base_cmd.BaseCmd)
    assert cmd_clone.CMD_NAME == "clone"
    assert cmd_clone.CMD_HELP == "Duplicate an existing Action related object (Function, Rule, Script, Message Destination, Workflow) with a new api or display name"
    assert cmd_clone.CMD_USAGE == """
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name> --changetype artifact
    $ resilient-sdk clone -f <function_to_be_cloned> <new_function_name>
    $ resilient-sdk clone -r "Display name of Rule" "Cloned Rule display name"
    $ resilient-sdk clone -s "Display name of Script" "Cloned Script display name"
    $ resilient-sdk clone -s "Display name of Script" "Cloned Script display name" --changetype task
    $ resilient-sdk clone -pre version2 -r "Display name of Rule 1" "Display name of Rule 2" -f <function_to_be_cloned> <function2_to_be_cloned>"""
    assert cmd_clone.CMD_DESCRIPTION == "Duplicate an existing Action related object (Function, Rule, Script, Message Destination, Workflow) with a new api or display name"


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
        Namespace(workflow=[old_name, new_name], changetype=""), TEST_EXPORT)

    original_obj = CmdClone.validate_provided_object_names(obj_type="workflows",
                                                           obj_identifier=ResilientObjMap.WORKFLOWS,
                                                           obj_type_name="Workflow",
                                                           new_object_api_name=new_name,
                                                           original_object_api_name=old_name,
                                                           export=TEST_EXPORT)
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.WORKFLOWS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.WORKFLOWS] != original_obj[
        ResilientObjMap.WORKFLOWS], "Expected that the export_key was updated"


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
    new_obj = CmdClone.replace_function_object_attrs(
        obj_to_modify, "test_new_function")

    assert new_obj[ResilientObjMap.FUNCTIONS] != old_function_name


def test_replace_workflow_object_attrs():
    """test_replace_workflow_object_attrs test to verify the functionality of replacing a workflows unique attributes
    """
    # Get the first workflow from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("workflows")[0])

    old_workflow_name = obj_to_modify[ResilientObjMap.WORKFLOWS]
    new_obj = copy.copy(obj_to_modify)
    new_obj = CmdClone.replace_workflow_object_attrs(
        obj_to_modify, obj_to_modify[ResilientObjMap.WORKFLOWS], "test_new_workflow", obj_to_modify['name'])

    assert new_obj[ResilientObjMap.WORKFLOWS] != old_workflow_name


def test_replace_rule_object_attrs():
    """test_replace_rule_object_attrs test to verify the functionality of replacing a rules unique attributes
    """
    # Get the first rule from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("actions")[0])

    old_rule_name = obj_to_modify[ResilientObjMap.RULES]
    new_obj = copy.copy(obj_to_modify)
    new_obj = CmdClone.replace_rule_object_attrs(
        obj_to_modify, "test_new_rule")

    assert new_obj[ResilientObjMap.RULES] != old_rule_name


def test_replace_md_object_attrs():
    """test_replace_md_object_attrs test to verify the functionality of replacing a message destinations unique attributes
    """
    # Get the first rule from the list
    obj_to_modify = copy.copy(TEST_EXPORT.get("message_destinations")[0])

    old_md_name = obj_to_modify[ResilientObjMap.MESSAGE_DESTINATIONS]
    new_obj = copy.copy(obj_to_modify)
    new_obj = CmdClone.replace_md_object_attrs(obj_to_modify, "fn_msg_dst")

    assert new_obj[ResilientObjMap.RULES] != old_md_name


def test_replace_common_object_attrs():
    """test_replace_common_object_attrs test to verify the functionality of replacing an action objects unique attributes

    :param fx_get_sub_parser: [description]
    :type fx_get_sub_parser: [type]
    """
    test_name = "My new name"
    original_uuid = TEST_OBJ['uuid']
    original_export_key = TEST_OBJ['export_key']
    new_object = CmdClone.replace_common_object_attrs(TEST_OBJ, test_name)
    assert new_object['name'] == test_name, "Expected name to be updated"
    assert new_object['uuid'] != original_uuid, "Expected uuid to be updated"
    assert new_object['export_key'] != original_export_key, "Expected export_key to be updated"


def test_action_obj_was_specified_not_present(fx_get_sub_parser, fx_cmd_line_args_clone_prefix):
    """
    Test to verify that if an action object is not specified in the args
    that action_obj_was_specified() returns False as expected
    """
    cmd_clone = CmdClone(fx_get_sub_parser)

    args = cmd_clone.parser.parse_known_args()[0]

    for functions in TEST_EXPORT.get('functions'):

        if functions['name'] not in args.function:
            assert not CmdClone.action_obj_was_specified(args, functions)


def test_action_obj_was_specified_success(fx_get_sub_parser, fx_cmd_line_args_clone_prefix):
    """
    Test to verify that if an action object is specified in the args
    that action_obj_was_specified() returns True as expected
    """
    cmd_clone = CmdClone(fx_get_sub_parser)

    args = cmd_clone.parser.parse_known_args()[0]
    function = TEST_EXPORT.get('functions')[0]

    for fn in TEST_EXPORT.get('functions'):
        if fn.get("name") == 'mock_function_one':
            function = fn
            break

    assert function['name'] == 'mock_function_one'
    assert CmdClone.action_obj_was_specified(args, function)


def test_clone_change_type(fx_get_sub_parser, fx_cmd_line_args_clone_typechange):
    """
    Test to verify when specifying the --changetype arg when cloning a workflow
    that the newly cloned workflow has its type changed as expected
    """

    cmd_clone = CmdClone(fx_get_sub_parser)

    args = cmd_clone.parser.parse_known_args()[0]
    assert args.changetype == "task"

    export_data = cmd_clone._clone_workflow(args, TEST_EXPORT)

    old_name, new_name = args.workflow
    original_obj = CmdClone.validate_provided_object_names(obj_type="workflows",
                                                           obj_identifier=ResilientObjMap.WORKFLOWS,
                                                           obj_type_name="Workflow",
                                                           new_object_api_name=new_name,
                                                           original_object_api_name=old_name,
                                                           export=TEST_EXPORT)
    assert export_data[0]['name'] != old_name, "Expected the returned export data to not have a reference to the old function"
    assert export_data[0][ResilientObjMap.WORKFLOWS] == new_name, "Expected the returned export to contain the new function name"
    # Ensure the Object specific primary key is not duplicated
    assert export_data[0][ResilientObjMap.WORKFLOWS] != original_obj[
        ResilientObjMap.WORKFLOWS], "Expected that the export_key was updated"

    assert export_data[0]['object_type'] == 'task', "Expected the new workflows object_type to be set to task"
    assert export_data[0]['object_type'] != original_obj['object_type'], "Expected the cloned workflow to have a different object type to before"


def test_clone_prefix(fx_get_sub_parser, fx_cmd_line_args_clone_prefix):
    """
    Test when calling 'clone' and specifying a prefix
    the prefix is found on all the cloned objects
    """

    cmd_clone = CmdClone(fx_get_sub_parser)

    args = cmd_clone.parser.parse_known_args()[0]

    # When running tox tox args are picked up by the parser
    # -s tests from the tox command passes `tests/` as a script name
    # If we have script args and tests is present, remove it.
    if args.script and 'tests/' in args.script:
        args.script.remove('tests/')
    # Assert the prefix arg was passed as expected
    assert args.prefix == "v2"

    # Copy the export data so we don't modify the existing object
    new_export_data = TEST_EXPORT.copy()

    # Sanitize the export dict to remove everything non essential before clone
    for dict_key in new_export_data:
        if dict_key not in MANDATORY_KEYS and isinstance(new_export_data[dict_key], list):
            # clear the new export data, the stuff we clear isn't necessary for cloning
            new_export_data[dict_key] = []

    # Perform the cloning
    cmd_clone._clone_multiple_action_objects(
        args, new_export_data, TEST_EXPORT)

    # A mapping table of the org_export items and their unique identifiers
    # for each tested type, get the type name in the export and its identifier
    for obj_type, identifier in EXPORT_TYPE_MAP.items():
        # for each action onject of type obj_type
        for obj in new_export_data[obj_type]:
            # Ensure the provided prefix is found on the objects unique identifier
            assert "v2" in obj[identifier], "Expected the object's identifer to contain the prefix"


def test_clone_multiple(fx_get_sub_parser, fx_cmd_line_args_clone_prefix):
    """
    Test when calling 'clone'  with multiple objects and specifying a prefix
    the resultant export object contains the appropiate number of cloned objects
    """
    cmd_clone = CmdClone(fx_get_sub_parser)

    args = cmd_clone.parser.parse_known_args()[0]

    # When running tox tox args are picked up by the parser
    # -s tests from the tox command passes `tests/` as a script name
    # If we have script args and tests is present, remove it.
    if args.script and 'tests/' in args.script:
        args.script.remove('tests/')

    # Assert the prefix arg was passed as expected
    assert args.prefix == "v2"
    # Copy the export data so we don't modify the existing object
    new_export_data = TEST_EXPORT.copy()

    # Sanitize the export dict to remove everything non essential before clone
    for dict_key in new_export_data:
        if dict_key not in MANDATORY_KEYS and isinstance(new_export_data[dict_key], list):
            # clear the new export data, the stuff we clear isn't necessary for cloning
            new_export_data[dict_key] = []
    # Perform the cloning
    cmd_clone._clone_multiple_action_objects(
        args, new_export_data, TEST_EXPORT)

    # Assert in the new export dict that there is the same number of objects
    # as there is in the args
    assert len(new_export_data['functions']) == len(args.function)
    assert len(new_export_data['workflows']) == len(args.workflow)
    assert len(new_export_data['actions']) == len(args.rule)


def test_clone_workflow_failure(fx_get_sub_parser, fx_cmd_line_args_clone_prefix):
    """
    Test when calling 'clone' command and providing a non existant source workflow
    that an exception is raised as expected and has the correct message
    """

    old_name = "non_existant_workflow"
    new_name = "new_mocked_workflow"
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
    expected_error = "Workflow: '{}' not found in this export.".format(
        old_name)
    with pytest.raises(SDKException) as excinfo:
        export_data = cmd_clone._clone_workflow(
            Namespace(workflow=[old_name, new_name], changetype=""), TEST_EXPORT)

        original_obj = CmdClone.validate_provided_object_names(obj_type="workflows",
                                                               obj_identifier=ResilientObjMap.WORKFLOWS,
                                                               obj_type_name="Workflow",
                                                               new_object_api_name=new_name,
                                                               original_object_api_name=old_name,
                                                               export=TEST_EXPORT)
    # Gather the message from the execution info, throwing away the other args
    exception_message, = excinfo.value.args
    assert expected_error in exception_message

@pytest.mark.parametrize("input_args, obj_type, obj_identifier, obj_name, replace_fn",
                         TEST_CLONE_FAILURE_DATA, ids=['Function', 'Rule', 'Message Destination', 'Scripts'])
def test_clone_action_obj_failure(fx_get_sub_parser, input_args, obj_type, obj_identifier, obj_name, replace_fn):
    """
    Parametrized tests to confirm for each scenario if a non-existant action object is provided
    an appropriate exception is raised with the expected message 
    """
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
    expected_error = "{}: '{}' not found in this export.".format(
        obj_type, input_args[0])
    with pytest.raises(SDKException) as excinfo:
        export_data = cmd_clone._clone_action_object(
            input_args, TEST_EXPORT, obj_type, obj_identifier, obj_name, replace_fn)
    # Gather the message from the execution info, throwing away the other args
    exception_message, = excinfo.value.args
    assert expected_error in exception_message


def test_clone_action_obj_too_many_args(fx_get_sub_parser):
    """
    Test scenario when more than 2 args are provided and no prefix is specified for cloning an exception is raised
    """
    # Get sub_parser object, its dest is cmd
    cmd_clone = CmdClone(fx_get_sub_parser)
    expected_error = "Did not receive the right amount of object names. Only expect 2 and 3 were given. Only specify the original action object name and a new object name"
    with pytest.raises(SDKException) as excinfo:
        export_data = cmd_clone._clone_action_object(
            ("thing1", "thing2", "thing3"), TEST_EXPORT, 'Fuction', ResilientObjMap.FUNCTIONS, 'functions', CmdClone.replace_function_object_attrs)
    # Gather the message from the execution info, throwing away the other args
    exception_message, = excinfo.value.args
    assert exception_message == expected_error
