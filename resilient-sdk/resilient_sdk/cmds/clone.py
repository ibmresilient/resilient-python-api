#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: implement clone """

import logging
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.helpers import (get_resilient_client, get_latest_org_export, 
                                        minify_export,get_from_export,
                                        get_object_api_names)
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util.sdk_exception import SDKException


# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

IMPORT_URL = "/configurations/imports"


class CmdClone(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "clone"
    CMD_HELP = "Duplicate an existing Action related object (Workflow, Function) with a new api nam"
    CMD_USAGE = """
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
    $ resilient-sdk clone -f <function_to_be_cloned> <new_function_name>
    CMD_DESCRIPTION = "Duplicate an existing Action related object (Workflow, Function) with a new api name"""
    CMD_USE_COMMON_PARSER_ARGS = True
    CMD_ADD_PARSERS = ["res_obj_parser"]

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--prefix",
                                 type=ensure_unicode,
                                 help="The prefix to be placed at the start of cloned  Action Objects. Used when cloning more than 1 of each Action Object Type.")

    def execute_command(self, args):
        """execute_command When the clone command is executed, we want to perform these actions:
        1: Setup a client to Resilient and get the latest export file.
        2: For each specified action type (Function, Workflow, Rule):
            2.1: Ensure the user provided both the source and new action name
            2.2: Check that the provided source action type exists and the new action name is unique.
            2.3: Prepare a new Object from the source action object replacing the names were needed.
        3: Prepare our configuration upload object with the newly cloned action objects
        4: Submit a configuration import through the API
        5: Confirm the change has been acceepted

        :param args: The command line args passed with the clone command such as workflows or functions to be cloned
        :type args: [type]
        :raises Exception: [description]
        :raises Exception: [description]
        :return: [description]
        :rtype: [type]
        """
        LOG.info("Called clone with %s", args)

        # Instansiate connection to the Resilient Appliance
        res_client = get_resilient_client()

        org_export = get_latest_org_export(res_client)

        # Copy the export data so we don't modify the existing object
        new_export_data = org_export.copy()

        whitelist_dict_keys = ["incident_types", "fields"]  # Mandatory keys
        for dict_key in new_export_data:
            if dict_key not in whitelist_dict_keys and isinstance(new_export_data[dict_key], list):
                # clear the new export data, the stuff we clear isn't necessary for cloning
                new_export_data[dict_key] = []
        # If any of the supported args are provided
        if any([args.function, args.workflow, args.rule, args.messagedestination]):
            if args.prefix:
                self._clone_multiple_action_objects(
                    args, new_export_data, org_export)

            else:

                if args.function:
                    self._clone_function(args, new_export_data, org_export)

                if args.rule:
                    self._clone_rule(args, new_export_data, org_export)

                if args.workflow:
                    self._clone_workflow(args, new_export_data, org_export)

                if args.messagedestination:
                    self._clone_message_destination(
                        args, new_export_data, org_export)

            self.upload_cloned_objects(new_export_data, res_client)

        else:
            self.parser.print_help()

    @staticmethod
    def upload_cloned_objects(new_export_data, res_client):
        # Import our newly cloned object with a configuration change
        try:
            result = res_client.post(IMPORT_URL, new_export_data)
        except Exception as e:
            LOG.error(result.text)
            LOG.error(new_export_data)
        if result["status"] == "PENDING":
            confirm_configuration_import(result, result['id'], res_client)
        else:
            raise Exception(
                "Could not import because the server did not return an import ID")

    def _clone_multiple_action_objects(self, args, new_export_data, org_export):
        LOG.info("Prefix provided, copying multiple Action Objects")
        # Get data required from the export
        jinja_data = get_from_export(org_export,
                                     message_destinations=args.messagedestination,
                                     functions=args.function,
                                     workflows=args.workflow,
                                     rules=args.rule,
                                     fields=args.field,
                                     artifact_types=args.artifacttype,
                                     datatables=args.datatable,
                                     tasks=args.task,
                                     scripts=args.script)
        # Get 'minified' version of the export. This is used in customize.py
        minified = minify_export(org_export,
                                 message_destinations=get_object_api_names(
                                     ResilientObjMap.MESSAGE_DESTINATIONS, jinja_data.get("message_destinations")),
                                 functions=get_object_api_names(
                                     ResilientObjMap.FUNCTIONS, jinja_data.get("functions")),
                                 workflows=get_object_api_names(
                                     ResilientObjMap.WORKFLOWS, jinja_data.get("workflows")),
                                 rules=get_object_api_names(
                                     ResilientObjMap.RULES, jinja_data.get("rules")),
                                 fields=jinja_data.get("all_fields"),
                                 artifact_types=get_object_api_names(
                                     ResilientObjMap.INCIDENT_ARTIFACT_TYPES, jinja_data.get("artifact_types")),
                                 datatables=get_object_api_names(
                                     ResilientObjMap.DATATABLES, jinja_data.get("datatables")),
                                 tasks=get_object_api_names(
                                     ResilientObjMap.TASKS, jinja_data.get("tasks")),
                                 phases=get_object_api_names(
                                     ResilientObjMap.PHASES, jinja_data.get("phases")),
                                 scripts=get_object_api_names(ResilientObjMap.SCRIPTS, jinja_data.get("scripts")))
        # For every thing in the export
        for object_type, action_objects in minified.items():
            # If the type is not fields and the value of the type is a list
            if object_type != "all_fields" and isinstance(action_objects, list):
                # Iterate over each object in the action_objects list
                for obj in action_objects:
                    # If the obj is not a dict, it is not an action object
                    if isinstance(obj, dict):
                        old_api_name = obj.get('export_key')
                        new_api_name = "{}_{}".format(
                            args.prefix, old_api_name)
                        # If the object we are dealing with was one of the requested objects
                        # TODO: Improve spacetime complexity and make generic for all supported types
                        if self.action_obj_was_specified(args, obj):
                            # Handle functions
                            if obj.get('display_name', False):
                                new_function = replace_function_object_attrs(
                                    obj, new_api_name)

                                LOG.info(new_function)
                                new_export_data['functions'].append(
                                    new_function)
                                # LOG.info(new_export_data)
                            # Handle workflows
                            elif obj.get('content', {}).get('xml', False):
                                new_export_data['workflows'].append(replace_workflow_object_attrs(
                                    obj, old_api_name, new_api_name, obj['name']))
                            # Handle Message Destination. Of the supported Action Object types; only Message Destination and Workflow use programmatic_name
                            elif obj.get('programmatic_name', False):
                                new_export_data['message_destinations'].append(replace_md_object_attrs(
                                    obj, new_api_name))
    
    @staticmethod
    def action_obj_was_specified(args, obj):
        
        return obj.get(ResilientObjMap.MESSAGE_DESTINATIONS, "") in args.messagedestination

    @staticmethod
    def _clone_message_destination(args, new_export_data, org_export):
        if len(args.messagedestination) != 2:
            raise SDKException(
                "Only specify the original message_destination name and a new message_destination name")
        original_md_api_name, new_md_api_name = args.messagedestination
        destinations_def = org_export.get(
            "message_destinations").copy()
        LOG.info(destinations_def)
        # TODO: Can this be refactored?
        duplicate_check = find_workflow_by_programmatic_name(
            destinations_def, new_md_api_name)
        if duplicate_check is not None:
            raise SDKException("Workflow with the api name {} already exists".format(
                new_md_api_name))
        # TODO: Can this be refactoed too ?
        original_md = find_workflow_by_programmatic_name(
            destinations_def, original_md_api_name)
        if original_md is None:
            raise SDKException("Could not find original workflow {}".format(
                original_md_api_name))
        new_message_destination = replace_md_object_attrs(
            original_md, new_md_api_name)
        new_export_data["message_destinations"] = [
            new_message_destination]

    @staticmethod
    def _clone_workflow(args, new_export_data, org_export):
        if len(args.workflow) != 2:
            raise Exception(
                "Only specify the original workflow api name and a new workflow api name")
        original_workflow_api_name, new_workflow_api_name = args.workflow

        # Get the workflow defintion objects
        workflow_defs = org_export.get("workflows")
        # Validate both the original source workflow exists and the new workflow api name does not conflict with an existing workflow
        original_workflow = CmdClone.validate_provided_object_names("Workflow", new_workflow_api_name,
                                                                    original_workflow_api_name, workflow_defs)
        new_workflow = original_workflow.copy()
        # Gather the old workflow name before we modify the object
        old_workflow_name = new_workflow["name"]
        # Update workflow specific items and any common obj attributes
        new_workflow = replace_workflow_object_attrs(
            new_workflow, original_workflow_api_name, new_workflow_api_name, old_workflow_name)
        # Add the cloned workflow to the new export object
        new_export_data["workflows"] = [new_workflow]
        return new_workflow_api_name, original_workflow_api_name

    @staticmethod
    def validate_provided_object_names(obj_type_name, new_workflow_api_name, original_workflow_api_name, workflow_defs):

        # Perform a duplication check with the provided new_workflow_api_name
        duplicate_check = find_workflow_by_programmatic_name(
            workflow_defs, new_workflow_api_name)

        if duplicate_check is not None:
            raise SDKException("{} with the api name {} already exists".format(
                obj_type_name, new_workflow_api_name))
        # Gather the original Action Object to be returned
        original_workflow = find_workflow_by_programmatic_name(
            workflow_defs, original_workflow_api_name)
        # Validate the provided workflow_api_name gathered an object
        if original_workflow is None:
            raise SDKException("Could not find original {} {}".format(
                obj_type_name, original_workflow_api_name))
        # Return the object
        return original_workflow

    @staticmethod
    def _clone_rule(args, new_export_data, org_export):
        if len(args.rule) != 2:
            raise Exception(
                "Only specify the original rule name and a new rule name")
        original_rule_api_name, new_rule_api_name = args.rule
        rule_defs = org_export.get("actions")
        # TODO: Can this be refactored?
        duplicate_check = find_workflow_by_programmatic_name(
            rule_defs, new_rule_api_name)
        if duplicate_check is not None:
            raise Exception(
                "Rule with the api name {} already exists".format(new_rule_api_name))
        # TODO: Can this be refactoed too ?
        original_rule = find_workflow_by_programmatic_name(
            rule_defs, original_rule_api_name)
        if original_rule is None:
            raise Exception("Could not find original rule {}".format(
                original_rule_api_name))
        # Update workflow specific items and any common obj attributes
        new_rule = replace_rule_object_attrs(
            original_rule.copy(), new_rule_api_name)
        # Add the cloned workflow to the new export object
        new_export_data["actions"] = [new_rule]

    @staticmethod
    def _clone_function(args, new_export_data, org_export):
        if len(args.function) != 2 and not args.prefix:
            raise Exception(
                "Only specify the original function api name and a new function api name")
        original_function_api_name, new_function_api_name = args.function
        function_defs = org_export.get("functions")
        # Get the function we are dealing with
        original_function = find_workflow_by_programmatic_name(
            function_defs, original_function_api_name)
        LOG.info(original_function)
        # Update workflow specific items and any common obj attributes
        new_function = replace_function_object_attrs(
            original_function.copy(), new_function_api_name)
        # Add the cloned workflow to the new export object
        new_export_data["functions"] = [new_function]


def confirm_configuration_import(result, import_id, res_client):
    try:
        result["status"] = "ACCEPTED"      # Have to confirm changes
        uri = "/configurations/imports/{}".format(import_id)
        res_client.put(uri, result, timeout=5)
        LOG.info("Imported successfully")
    except Exception as e:
        LOG.error(result)
        LOG.error(repr(e))


def find_workflow_by_programmatic_name(workflows, pname):
    for workflow in workflows:
        if workflow.get("programmatic_name") == pname or workflow.get("export_key") == pname:
            return workflow

    return None


def replace_common_object_attrs(obj_to_modify, new_obj_api_name):
    """replace_common_object_attrs A function used to update the most common fields for an Action Object.
    When cloning an Action Object, depending on the type of that object certain fields will need to be overwritten.
    In most cases the name, export_key and uuid will always need to be changed to prevent duplication errors.

    :param obj_to_modify: The Action Object we are replacing values for 
    :type obj_to_modify: dict
    :param original_obj_api_name: the API name of the Action Object we are cloning
    :type original_obj_api_name: string
    :param new_obj_api_name: the API name for the new cloned Action Object
    :type new_obj_api_name: string
    :return: A modified Action Object which can be imported to Resilient
    :rtype: dict
    """
    import uuid
    obj_to_modify.update(
        {
            "uuid": str(uuid.uuid4()),
            "export_key": new_obj_api_name,
            "name": new_obj_api_name
        }
    )
    return obj_to_modify


def replace_workflow_object_attrs(obj_to_modify, original_obj_api_name, new_obj_api_name, old_workflow_name):
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    # Now do the workflow specific ones and return
    obj_to_modify.update({
        ResilientObjMap.WORKFLOWS: original_obj_api_name,
        "content": {
            "xml": obj_to_modify["content"]["xml"].replace(
                original_obj_api_name,
                new_obj_api_name).replace(
                    old_workflow_name,
                    new_obj_api_name),
            "workflow_id": new_obj_api_name
        }})
    return obj_to_modify


def replace_function_object_attrs(obj_to_modify, new_obj_api_name):
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    # # Now do the workflow specific ones and return
    obj_to_modify.update({
        "display_name": new_obj_api_name,
        ResilientObjMap.FUNCTIONS: new_obj_api_name
    })
    return obj_to_modify


def replace_rule_object_attrs(obj_to_modify, new_obj_api_name):
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    return obj_to_modify


def replace_md_object_attrs(obj_to_modify, new_obj_api_name):
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)
    obj_to_modify.update({
        ResilientObjMap.MESSAGE_DESTINATIONS: new_obj_api_name
    })
    return obj_to_modify
