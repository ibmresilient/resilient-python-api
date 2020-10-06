#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk clone` """

import logging
import uuid
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_helpers import (get_resilient_client, get_latest_org_export,
                                            minify_export, get_from_export,
                                            get_object_api_names, add_configuration_import)
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util.sdk_exception import SDKException


# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

MANDATORY_KEYS = ["incident_types", "fields"]  # Mandatory keys for a configuration import



class CmdClone(BaseCmd):
    """
    resilient-sdk clone allows you to 'clone' Resilient Objects
    from a Resilient Export
    It will modify the unique identifier of the specified Resilient Objects
    and make an configuration import request to complete the cloning process"""

    CMD_NAME = "clone"
    CMD_HELP = "Duplicate an existing Action related object (Workflow, Function) with a new api name"
    CMD_USAGE = """
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
    $ resilient-sdk clone -f <function_to_be_cloned> <new_function_name>"""
    CMD_DESCRIPTION = "Duplicate an existing Action related object (Workflow, Function) with a new api name"
    CMD_USE_COMMON_PARSER_ARGS = True
    CMD_ADD_PARSERS = ["res_obj_parser"]

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-pre", "--prefix",
                                 type=ensure_unicode,
                                 help="The prefix to be placed at the start of cloned Action Objects. Used when cloning more than 1 of each Action Object Type.")
        self.parser.add_argument("-type", "--changetype",
                                type=ensure_unicode,
                                help="The new type of the clone action object. Used when cloning a workflow to have the newly cloned workflow at a different object type.")

    def execute_command(self, args):
        """ 
        When the clone command is executed, we want to perform these actions:
        1: Setup a client to Resilient and get the latest export file.
        2: For each specified action type (Function, Workflow, Rule):
            2.1: Ensure the user provided both the source and new action name
            2.2: Check that the provided source action type exists and the new action name is unique.
            2.3: Prepare a new Object from the source action object replacing the names were needed.
        3: Prepare our configuration import object for upload with the newly cloned action objects
        4: Submit a configuration import through the API
        5: Confirm the change has been accepted

        :param args: The command line args passed with the clone command of Resilient Objects to be cloned
        :type args: [type]
        :raises SDKException: [description]
        :return: [description]
        :rtype: [type]
        """
        LOG.info("Called clone with %s", args)

        # Instansiate connection to the Resilient Appliance
        res_client = get_resilient_client()

        org_export = get_latest_org_export(res_client)


        # Copy the export data so we don't modify the existing object
        new_export_data = org_export.copy()

        for dict_key in new_export_data:
            if dict_key not in MANDATORY_KEYS and isinstance(new_export_data[dict_key], list):
                # clear the new export data, the stuff we clear isn't necessary for cloning
                new_export_data[dict_key] = []
        # If any of the supported args are provided
        if any([args.function, args.workflow, args.rule, args.messagedestination]):
            if args.prefix:
                self._clone_multiple_action_objects(
                    args, new_export_data, org_export)

            else:

                if args.function:
                    new_export_data['functions'] = self._clone_action_object(
                        args.function, org_export, 'Function', 'functions', replace_function_object_attrs)

                if args.rule:
                    new_export_data["actions"] = self._clone_action_object(
                        args.rule, org_export, 'Rule', 'actions', replace_rule_object_attrs)

                if args.workflow:
                    new_export_data["workflows"] = self._clone_workflow(
                        args, org_export)

                if args.messagedestination:
                    new_export_data["message_destinations"] = self._clone_action_object(
                        args.messagedestination, org_export, 'Message Destination', 'message_destinations', replace_md_object_attrs)

            add_configuration_import(new_export_data, res_client)

        else:
            self.parser.print_help()


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
                # Iterate over each object in the filtered action_objects list. If the obj is not a dict, it is not an action object
                for obj in filter(lambda obj: isinstance(obj, dict), action_objects):
                    old_api_name = obj.get('export_key')
                    new_api_name = "{}_{}".format(
                        args.prefix, old_api_name)
                    # If the object we are dealing with was one of the requested objects
                    if self.action_obj_was_specified(args, obj):
                        # Handle functions and datatables
                        if obj.get('display_name', False):
                            new_function = replace_function_object_attrs(
                                obj, new_api_name)

                            new_export_data[object_type].append(new_function)
                        # Handle workflows
                        elif obj.get('content', {}).get('xml', False):
                            new_export_data['workflows'].append(replace_workflow_object_attrs(
                                obj, old_api_name, new_api_name, obj['name']))
                        # Handle Message Destination. Of the supported Action Object types; only Message Destination and Workflow use programmatic_name
                        elif obj.get('programmatic_name', False):
                            new_export_data['message_destinations'].append(replace_md_object_attrs(
                                obj, new_api_name))
                        # Handle Rules and everything else
                        else:
                            new_export_data[object_type].append(replace_rule_object_attrs(
                                obj, new_api_name))

    @staticmethod
    def action_obj_was_specified(args, obj):
        """
        Function used to perform a check that the provided obj was specified

        Iterates over the supported types, for each add the specified objs to a list
        Finally perform a check that the given identifier key is found in the object
        """
        # TODO: Message destination is not supported due to an issue where if its specified with a function all functions are copyed
        supported_types = ['function', 'workflow', 'rule', 'datatable']

        specified_objs = []
        for type_name in supported_types:
            # Use getattr to get each arg on the Namespace Object
            if getattr(args, type_name):
                specified_objs.extend(getattr(args, type_name))

        specified_objs = set(specified_objs)

        # Functions contain a reference to the message destination, for this case check and handle functions first
        if obj.get('destination_handle', False):
            return obj.get(ResilientObjMap.FUNCTIONS, "") in specified_objs
        return obj.get(ResilientObjMap.RULES, "") in specified_objs or obj.get(ResilientObjMap.WORKFLOWS, "") in specified_objs or obj.get(ResilientObjMap.FUNCTIONS, "") in specified_objs or obj.get(ResilientObjMap.DATATABLES, "") in specified_objs

    @staticmethod
    def _clone_action_object(input_args, org_export, obj_name, obj_key, replace_fn):
        if len(input_args) != 2:
            raise SDKException(
                "Received less than 2 object names. Only specify the original action object name and a new object name")

        original_obj_api_name, new_obj_api_name = input_args

        obj_defs = org_export.get(obj_key)
        original_obj = CmdClone.validate_provided_object_names(obj_name, new_obj_api_name,
                                                    original_obj_api_name, obj_defs)

        cloned_object = replace_fn(original_obj.copy(), new_obj_api_name)

        return [cloned_object]
    
    @staticmethod
    def _clone_message_destination(args, org_export):
        if len(args.messagedestination) != 2:
            raise SDKException(
                "Only specify the original message_destination name and a new message_destination name")
        original_md_api_name, new_md_api_name = args.messagedestination
        # Get the md defintion objects
        destinations_def = org_export.get(
            "message_destinations")
        LOG.info(destinations_def)
        # Validate both the original source md exists and the new md api name does not conflict with an existing md
        original_md = CmdClone.validate_provided_object_names("Message Destination", new_md_api_name,
                                                              original_md_api_name, destinations_def)
        # Update md specific items and any common obj attributes
        new_message_destination = replace_md_object_attrs(
            original_md.copy(), new_md_api_name)

        return [new_message_destination]

    @staticmethod
    def _clone_workflow(args, org_export):
        if len(args.workflow) != 2:
            raise SDKException(
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

        # If type was provided, change the workflows type 
        # TODO: Only supported on workflow cloning, in future review which objects benefit most from type changing
        if args.changetype:
            new_workflow['object_type'] = args.changetype
        # Add the cloned workflow to the new export object
        return [new_workflow]

    @staticmethod
    def validate_provided_object_names(obj_type_name, new_workflow_api_name, original_workflow_api_name, workflow_defs):

        # Perform a duplication check with the provided new_workflow_api_name
        duplicate_check = find_res_obj_by_identifier(
            workflow_defs, new_workflow_api_name)

        if duplicate_check is not None:
            raise SDKException("{} with the api name {} already exists".format(
                obj_type_name, new_workflow_api_name))
        # Gather the original Action Object to be returned
        original_workflow = find_res_obj_by_identifier(
            workflow_defs, original_workflow_api_name)
        # Validate the provided workflow_api_name gathered an object
        if original_workflow is None:
            raise SDKException("Could not find original {} {}".format(
                obj_type_name, original_workflow_api_name))
        # Return the object
        return original_workflow

    @staticmethod
    def _clone_rule(args, org_export):
        if len(args.rule) != 2:
            raise SDKException(
                "Only specify the original rule name and a new rule name")
        original_rule_api_name, new_rule_api_name = args.rule
        rule_defs = org_export.get("actions")
        # Validate both the original source rule exists and the new rule api name does not conflict with an existing rule
        original_rule = CmdClone.validate_provided_object_names("Rule", new_rule_api_name,
                                                                original_rule_api_name, rule_defs)
        # Update workflow specific items and any common obj attributes
        new_rule = replace_rule_object_attrs(
            original_rule.copy(), new_rule_api_name)
        # Return the new rule in list form
        return [new_rule]

    @staticmethod
    def _clone_function(args, org_export):
        if len(args.function) != 2 and not args.prefix:
            raise SDKException(
                "Only specify the original function api name and a new function api name")
        original_function_api_name, new_function_api_name = args.function
        function_defs = org_export.get("functions")
        # Validate both the original source function exists and the new function api name does not conflict with an existing function
        original_function = CmdClone.validate_provided_object_names("Function", new_function_api_name,
                                                                    original_function_api_name, function_defs)
        # Update workflow specific items and any common obj attributes
        new_function = replace_function_object_attrs(
            original_function.copy(), new_function_api_name)
        # Add the cloned workflow to the new export object
        return [new_function]



def find_res_obj_by_identifier(objects_list, identifier_value):
    for action_object in objects_list:
        if action_object.get(ResilientObjMap.DATATABLES) == identifier_value \
                or action_object.get(ResilientObjMap.FUNCTIONS) == identifier_value \
                or action_object.get(ResilientObjMap.RULES) == identifier_value \
                or action_object.get(ResilientObjMap.WORKFLOWS) == identifier_value:
            return action_object

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
    obj_to_modify.update(
        {
            "uuid": str(uuid.uuid4()),
            "export_key": new_obj_api_name,
            "name": new_obj_api_name
        }
    )
    return obj_to_modify


def replace_workflow_object_attrs(obj_to_modify, original_obj_api_name, new_obj_api_name, old_workflow_name):
    """replace_workflow_object_attrs replace/overwrite the unique attributes of the workflow object so that 
    the provided object can be cloned with a new name and not cause a conflict on upload.

    :param obj_to_modify: The object whose attributes will be modified, in this case a workflow
    :type obj_to_modify: dict
    :param original_obj_api_name: the name of the workflow to clone
    :type original_obj_api_name: str
    :param new_obj_api_name: the new cloned workflow name
    :type new_obj_api_name: str
    :param old_workflow_name: workflows have api names and also a name in the content object 
    :type old_workflow_name: str
    :return: the modified object
    :rtype: dict
    """
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    # Now do the workflow specific ones and return
    obj_to_modify.update({
        ResilientObjMap.WORKFLOWS: new_obj_api_name,
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
    """replace_function_object_attrs replace/overwrite the unique attributes of the workflow object so that
    the provided object can be cloned with a new name and not cause a conflict on upload.

    :param obj_to_modify: the object to be modified, in this case a function
    :type obj_to_modify: dict
    :param new_obj_api_name: the name of the function to modify
    :type new_obj_api_name: str
    :return: the modified object
    :rtype: dict
    """
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    # # Now do the workflow specific ones and return
    obj_to_modify.update({
        "display_name": new_obj_api_name,
        ResilientObjMap.FUNCTIONS: new_obj_api_name
    })
    if obj_to_modify.get(ResilientObjMap.DATATABLES, False):
        obj_to_modify.update({
            ResilientObjMap.DATATABLES: new_obj_api_name
        })
    return obj_to_modify


def replace_rule_object_attrs(obj_to_modify, new_obj_api_name):
    """replace_rule_object_attrs replace/overwrite the unique attributes of the rule object so that
    the provided object can be cloned with a new name and not cause a conflict on upload.

    :param obj_to_modify: the object to be modified, in this case a function
    :type obj_to_modify: dict
    :param new_obj_api_name: the name of the function to modify
    :type new_obj_api_name: str
    :return: the modified object
    :rtype: dict
    """
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)

    return obj_to_modify


def replace_md_object_attrs(obj_to_modify, new_obj_api_name):
    """replace_md_object_attrs replace/overwrite the unique attributes of the message destination object so that
    the provided object can be cloned with a new name and not cause a conflict on upload.

    :param obj_to_modify: the object to be modified, in this case a function
    :type obj_to_modify: dict
    :param new_obj_api_name: the name of the function to modify 
    :type new_obj_api_name: str
    :return: the modified object
    :rtype: dict
    """
    # Replace all the attributes which are common to most objects
    obj_to_modify = replace_common_object_attrs(
        obj_to_modify, new_obj_api_name)
    obj_to_modify.update({
        ResilientObjMap.MESSAGE_DESTINATIONS: new_obj_api_name
    })
    return obj_to_modify
