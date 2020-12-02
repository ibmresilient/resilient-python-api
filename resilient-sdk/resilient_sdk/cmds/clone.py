#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk clone` """

import logging
import uuid
import time
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_helpers import (get_resilient_client, get_latest_org_export,
                                            minify_export, get_from_export,
                                            get_object_api_names, add_configuration_import, get_res_obj)
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util.sdk_exception import SDKException


# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

# Mandatory keys for a configuration import
MANDATORY_KEYS = ["incident_types", "fields"]
SUPPORTED_ACTION_OBJECTS = ['function', 'workflow',
                            'rule', 'messagedestination', 'script']
ACTION_OBJECT_KEYS = ['functions', 'workflows',
                      'actions', 'message_destinations', 'scripts']

resilient_export_obj_mapping = {
    'workflows': ResilientObjMap.WORKFLOWS,
    'functions': ResilientObjMap.FUNCTIONS,
    'actions': ResilientObjMap.RULES,
    'message_destinations': ResilientObjMap.MESSAGE_DESTINATIONS,
    'scripts': ResilientObjMap.SCRIPTS,
}
resilient_msg_dest_auth_info = {
    "api_keys": {},
    "users": {}
}


class CmdClone(BaseCmd):
    """
    resilient-sdk clone allows you to 'clone' Resilient Objects
    from a Resilient Export
    It will modify the unique identifier of the specified Resilient Objects
    and make an configuration import request to complete the cloning process"""

    CMD_NAME = "clone"
    CMD_HELP = "Duplicate an existing Action related object (Function, Rule, Script, Message Destination, Workflow) with a new api or display name"
    CMD_USAGE = """
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name>
    $ resilient-sdk clone --workflow <workflow_to_be_cloned> <new_workflow_name> --changetype artifact
    $ resilient-sdk clone -f <function_to_be_cloned> <new_function_name>
    $ resilient-sdk clone -r "Display name of Rule" "Cloned Rule display name"
    $ resilient-sdk clone -s "Display name of Script" "Cloned Script display name"
    $ resilient-sdk clone -s "Display name of Script" "Cloned Script display name" --changetype task
    $ resilient-sdk clone -pre version2 -r "Display name of Rule 1" "Display name of Rule 2" -f <function_to_be_cloned> <function2_to_be_cloned>"""
    CMD_DESCRIPTION = "Duplicate an existing Action related object (Function, Rule, Script, Message Destination, Workflow) with a new api or display name"

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Arguments for action objects which support cloning
        self.parser.add_argument("-f", "--function",
                                 type=ensure_unicode,
                                 help="API names of functions to include",
                                 nargs="*")

        self.parser.add_argument("-m", "--messagedestination",
                                 type=ensure_unicode,
                                 help="API names of message destinations to include",
                                 nargs="*")

        self.parser.add_argument("-r", "--rule",
                                 type=ensure_unicode,
                                 help="Display names of rules to include (surrounded by \"\")",
                                 nargs="*")

        self.parser.add_argument("-s", "--script",
                                 type=ensure_unicode,
                                 help="Display names of scripts to include (surrounded by \"\")",
                                 nargs="*")

        self.parser.add_argument("-w", "--workflow",
                                 type=ensure_unicode,
                                 help="API names of workflows to include",
                                 nargs="*")

        # Additional arguments for different cloning operations
        # Prefix is used to specify multiple objects of the same type will be cloned and
        # the prefix is a string attached to the start of the existing action object name
        # the prefix + the existing object name becomes the cloned objects name
        self.parser.add_argument("-pre", "--prefix",
                                 type=ensure_unicode,
                                 help="The prefix to be placed at the start of cloned Action Objects. Used when cloning more than 1 of each Action Object Type.")
        # Scripts and Workflows support changing the type with the optional --changetype argument
        # this argument is used to change a Incident workflow to a task one or a artifact script
        # to an incident script.
        self.parser.add_argument("-type", "--changetype",
                                 type=ensure_unicode,
                                 help="The new type of the clone action object. Used when cloning a workflow or script to have the newly cloned workflow at a different object type.")

    def execute_command(self, args):
        """
        When the clone command is executed, we want to perform these actions:
        1: Setup a client to Resilient and get the latest export file.
        2: Cloning a single object per type: For each specified action type:
            2.1: Ensure the user provided both the source and new action name
            2.2: Check that the provided source action type exists and the new action name is unique.
            2.3: Prepare a new Object from the source action object replacing the names as needed.
        3: Cloning multiple objects with a prefix: For each specified action type:
            3.1: Ensure the user provided source action objects which exist
            3.2: Prepend the prefix to the unique identifiers for each object
        3: Prepare our configuration import object for upload with the newly cloned action objects
        4: Submit a configuration import through the API
        5: Confirm the change has been accepted

        :param args: The command line args passed with the clone command of Resilient Objects to be cloned
        :type args: argparse.ArgumentParser.Namespace
        :raises SDKException: An SDKException detailing what failed in the operation
        """
        SDKException.command_ran = "clone"
        LOG.debug("Called clone with %s", args)
        start = time.perf_counter()

        # Instansiate connection to the Resilient Appliance
        CmdClone.res_client = get_resilient_client()

        org_export = get_latest_org_export(CmdClone.res_client)

        # For the new export data DTO minify the export to only its mandatory attributes
        new_export_data = minify_export(org_export)

        # If any of the supported args are provided
        if any([args.function, args.workflow, args.rule, args.messagedestination, args.script]):
            if args.prefix:
                self._clone_multiple_action_objects(
                    args, new_export_data, org_export)

            else:

                if args.script:
                    # If a Script was provided, call _clone_action_object with Script related params and
                    # add the newly cloned Script to new_export_data
                    new_export_data['scripts'] = self._clone_action_object(
                        args.script, org_export, 'Script', ResilientObjMap.SCRIPTS, 'scripts', CmdClone.replace_common_object_attrs, args.changetype)
                if args.function:
                    # If a Function was provided, call _clone_action_object with Function related params and
                    # add the newly cloned Function to new_export_data
                    new_export_data['functions'] = self._clone_action_object(
                        args.function, org_export, 'Function', ResilientObjMap.FUNCTIONS, 'functions', CmdClone.replace_function_object_attrs)

                if args.rule:
                    # If a Rule was provided, call _clone_action_object with Rule related params and
                    # add the newly cloned Rule to new_export_data
                    new_export_data["actions"] = self._clone_action_object(
                        args.rule, org_export, 'Rule', ResilientObjMap.RULES, 'actions', CmdClone.replace_rule_object_attrs, new_object_type=args.changetype)

                if args.workflow:
                    # If a Workflow was provided, call _clone_workflow with Workflow related params and
                    # add the newly cloned Workflow to new_export_data
                    new_export_data["workflows"] = self._clone_workflow(
                        args, org_export)

                if args.messagedestination:
                    # If a Message Destination was provided, call _clone_action_object with Message Destination related params and
                    # add the newly cloned Message Destination to new_export_data
                    new_export_data["message_destinations"] = self._clone_action_object(
                        args.messagedestination, org_export, 'Message Destination', ResilientObjMap.MESSAGE_DESTINATIONS, 'message_destinations', CmdClone.replace_md_object_attrs)

            add_configuration_import(new_export_data, CmdClone.res_client)
            # If any message destinations were cloned, after creation attach a Authorised User or API Key
            # to the destination. Providing this info in the Configurations API call above will be ignored.
            self.add_authorised_info_to_md(new_export_data)

        else:
            self.parser.print_help()

        end = time.perf_counter()
        LOG.info("'clone' command finished in {} seconds".format(end - start))

    def add_authorised_info_to_md(self, new_export_data):
        """ 
        Function which takes a ConfigurationDTO and makes an API call to get all created message destinations
        For any created message destinations which are found in the configuration export iterate over it 
        and add either an API Key or a User ID to each. 
        Then make a PUT API call to attach this auth info to each destination that
        was created by the ConfigurationDTO 
        :param new_export_data: A ConfigurationDTO specifying objects which were imported into resilient
        :type new_export_data: dict
        """
        # Get all the names fo each newly cloned message destination
        newly_cloned_dests_names = [dest.get("programmatic_name") for dest in new_export_data.get("message_destinations", [])]
        # Make an API call and return a list of message_destinations whose name is found in our list newly cloned destination names
        destination_objects = [dest for dest in CmdClone.res_client.get("/message_destinations")["entities"] if dest['programmatic_name'] in newly_cloned_dests_names]
        # For each newly cloned object
        for cloned_object in destination_objects:
            # Inner function used with the get_put api call
            def update_user(dest):
                # Gather the API keys and users for the original copy of this cloned destination 
                # and append to the destination object
                if resilient_msg_dest_auth_info['api_keys'].get(cloned_object['name']):
                    dest["api_keys"].extend(resilient_msg_dest_auth_info['api_keys'].get(cloned_object['name']))
                if resilient_msg_dest_auth_info['users'].get(cloned_object['name']):
                    dest["users"].extend(resilient_msg_dest_auth_info['users'].get(cloned_object['name']))

                return dest

            dest_id = cloned_object["id"]
            uri = "/message_destinations/{}".format(dest_id)
            CmdClone.res_client.get_put(uri, update_user)

    def _clone_multiple_action_objects(self, args, new_export_data, org_export):
        LOG.info("Prefix provided {}, copying multiple Action Objects".format(args.prefix))

        # Get data required from the export
        jinja_data = get_from_export(org_export,
                                     message_destinations=args.messagedestination,
                                     functions=args.function,
                                     workflows=args.workflow,
                                     rules=args.rule,
                                     scripts=args.script,
                                     get_related_objects=False)
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
                                 scripts=get_object_api_names(ResilientObjMap.SCRIPTS, jinja_data.get("scripts")))

        # For each support object
        for object_type in ACTION_OBJECT_KEYS:
            for obj in minified.get(object_type, []):
                old_api_name = obj.get('export_key')
                new_api_name = "{}_{}".format(
                    args.prefix, old_api_name)
                # If the object we are dealing with was one of the requested objects
                if self.action_obj_was_specified(args, obj):
                    # Ensure the new_api_name for each object is unique, raise an Exception otherwise
                    CmdClone.perform_duplication_check(object_type, resilient_export_obj_mapping.get(object_type), "Object", new_api_name, org_export)
                        
                    # Handle functions for cloning
                    if obj.get('display_name', False):
                        new_function = CmdClone.replace_function_object_attrs(
                            obj, new_api_name)

                        new_export_data[object_type].append(new_function)
                    # Handle workflows for cloning
                    elif obj.get('content', {}).get('xml', False):
                        new_export_data['workflows'].append(CmdClone.replace_workflow_object_attrs(
                            obj, old_api_name, new_api_name, obj['name'], args.changetype))
                    # Handle Message Destination. Of the supported Action Object types; only Message Destination and Workflow use programmatic_name
                    elif obj.get('programmatic_name', False):
                        if obj.get('api_keys', False) and obj.get('users', False):
                            # Save the User and API key auth for upload after initial clone
                            resilient_msg_dest_auth_info['users'].update({
                                obj['name']: obj['users']
                            })
                            resilient_msg_dest_auth_info['api_keys'].update({
                                obj['name']: obj['api_keys']
                            })
                        new_export_data['message_destinations'].append(CmdClone.replace_md_object_attrs(
                            obj, new_api_name))
                    # Handle Rules and everything else
                    else:
                        new_export_data[object_type].append(CmdClone.replace_rule_object_attrs(
                            obj, new_api_name, args.changetype))

    @staticmethod
    def action_obj_was_specified(args, obj):
        """
        Function used to perform a check that the provided obj was specified

        Iterates over the supported types, for each add the specified objs to a list
        Finally perform a check that the given identifier key is found in the object
        """

        specified_objs = []
        for type_name in SUPPORTED_ACTION_OBJECTS:
            # Use getattr to get each arg on the Namespace Object
            if getattr(args, type_name):
                specified_objs.extend(getattr(args, type_name))

        # Functions contain a reference to the message destination, for this case check and handle functions first
        if obj.get('destination_handle', False):
            return obj.get(ResilientObjMap.FUNCTIONS, "") in specified_objs
        return any([obj.get(ResilientObjMap.RULES, "") in specified_objs, obj.get(ResilientObjMap.WORKFLOWS, "") in specified_objs, obj.get(ResilientObjMap.FUNCTIONS, "") in specified_objs, obj.get(ResilientObjMap.DATATABLES, "") in specified_objs])

    @staticmethod
    def _clone_action_object(input_args, org_export, obj_name, obj_identifier, obj_key, replace_fn, new_object_type=None):
        CmdClone.validate_provided_args_length(input_args)

        original_obj_api_name, new_obj_api_name = input_args

        original_obj = CmdClone.validate_provided_object_names(obj_type=obj_key,
                                                               obj_identifier=obj_identifier,
                                                               obj_type_name=obj_name,
                                                               new_object_api_name=new_obj_api_name,
                                                               original_object_api_name=original_obj_api_name,
                                                               export=org_export)

        cloned_object = replace_fn(original_obj.copy(), new_obj_api_name)
        if new_object_type:
            cloned_object['object_type'] = new_object_type

        if obj_name == "Message Destination":
            # Save the User and API key auth for upload after initial clone
            resilient_msg_dest_auth_info['users'].update({
                cloned_object['name']: original_obj['users']
            })
            resilient_msg_dest_auth_info['api_keys'].update({
                cloned_object['name']: original_obj['api_keys']
            })
        
        return [cloned_object]

    @staticmethod
    def _clone_workflow(args, org_export):
        CmdClone.validate_provided_args_length(args.workflow)
        original_workflow_api_name, new_workflow_api_name = args.workflow

        # Validate both the original source workflow exists and the new workflow api name does not conflict with an existing workflow
        original_workflow = CmdClone.validate_provided_object_names(obj_type="workflows",
                                                                    obj_identifier=ResilientObjMap.WORKFLOWS,
                                                                    obj_type_name="Workflow",
                                                                    new_object_api_name=new_workflow_api_name,
                                                                    original_object_api_name=original_workflow_api_name,
                                                                    export=org_export)
        new_workflow = original_workflow.copy()
        # Gather the old workflow name before we modify the object
        old_workflow_name = new_workflow["name"]

        # Update workflow specific items and any common obj attributes
        new_workflow = CmdClone.replace_workflow_object_attrs(
            new_workflow, original_workflow_api_name, new_workflow_api_name, old_workflow_name, args.changetype)

        # Add the cloned workflow to the new export object
        return [new_workflow]

    @staticmethod
    def perform_duplication_check(obj_type, obj_identifier, obj_type_name, new_object_api_name, export):
        """Attempt to get the referenced object from the org_export
        If the object is not found, return True.
        If the object is found, raise an SDK Exception specifying the provided object name is not unique
        and already exists on the system. 

        :param obj_type: The type name in the org export to search 
        :type obj_type: str
        :param obj_identifier: The identifier for the given object
        :type obj_identifier: str
        :param obj_type_name: [description]
        :type obj_type_name: str
        :param new_object_api_name: [description]
        :type new_object_api_name: str
        :param export: The org export to search through
        :type export: dict
        :raises SDKException: If the provided object name is found then this function raises a SDK exception specifying this must be unique. 
        """
        # Perform a duplication check with the provided new name
        try:
            # Try to get a res obj with the new name
            get_res_obj(obj_type, obj_identifier, obj_type_name, [
                        new_object_api_name], export, include_api_name=False)
        except SDKException:
            # get_res_obj raises an exception if the object is not found
            # normally this is good but for this unique use case
            # we expect that the object will not be found and so catch and release the raised SDKException
            return True
        else:
            # if get_res_obj does not raise an exception it means an object with that identifier exists
            # and in this case we raise an SDKException as the new name provided for cloning needs to be unique
            raise SDKException("The new name for a cloned object needs to be unique and a {} with the api name {} already exists".format(
                obj_type_name, new_object_api_name))

    @staticmethod
    def validate_provided_object_names(obj_type, obj_identifier, obj_type_name, new_object_api_name, original_object_api_name, export):

        CmdClone.perform_duplication_check(obj_type, obj_identifier, obj_type_name, new_object_api_name, export)

        # Gather the original Action Object to be returned
        original_object = get_res_obj(obj_type, obj_identifier, obj_type_name, [
                                        original_object_api_name], export, include_api_name=False)[0]
        # Return the object
        return original_object

    @staticmethod
    def validate_provided_args_length(input_args):
        if len(input_args) != 2:
            raise SDKException(
                "Did not receive the right amount of object names. Only expect 2 and {} were given. Only specify the original action object name and a new object name".format(len(input_args)))

    @staticmethod
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

    @staticmethod
    def replace_workflow_object_attrs(obj_to_modify, original_obj_api_name, new_obj_api_name, old_workflow_name, changetype=None):
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
        :param changetype: A new type for the workflow or None
        :type changetype: str or None
        :return: the modified object
        :rtype: dict
        """
        # Replace all the attributes which are common to most objects
        obj_to_modify = CmdClone.replace_common_object_attrs(
            obj_to_modify, new_obj_api_name)

        workflow_xml = obj_to_modify.get("content").get("xml")

        workflow_xml = workflow_xml.replace(u'id="{}"'.format(
            original_obj_api_name), u'id="{}"'.format(new_obj_api_name))
        workflow_xml = workflow_xml.replace(u'name="{}"'.format(
            old_workflow_name), u'name="{}"'.format(new_obj_api_name))
        # Now do the workflow specific ones and return
        obj_to_modify.update({
            ResilientObjMap.WORKFLOWS: new_obj_api_name,
            "content": {
                "xml": workflow_xml,
                "workflow_id": new_obj_api_name
            }})

        if changetype and obj_to_modify.get("object_type", False):
            obj_to_modify.update({
                "object_type": changetype
            })
        return obj_to_modify

    @staticmethod
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
        obj_to_modify = CmdClone.replace_common_object_attrs(
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

    @staticmethod
    def replace_rule_object_attrs(obj_to_modify, new_obj_api_name, changetype=None):
        """replace_rule_object_attrs replace/overwrite the unique attributes of the rule object so that
        the provided object can be cloned with a new name and not cause a conflict on upload.

        :param obj_to_modify: the object to be modified, in this case a function
        :type obj_to_modify: dict
        :param new_obj_api_name: the name of the function to modify
        :type new_obj_api_name: str
        :param changetype: A new type for the workflow or None
        :type changetype: str or None
        :return: the modified object
        :rtype: dict
        """
        # Replace all the attributes which are common to most objects
        obj_to_modify = CmdClone.replace_common_object_attrs(
            obj_to_modify, new_obj_api_name)

        if changetype and obj_to_modify.get("object_type", False):
            obj_to_modify.update({
                "object_type": changetype
            })
        return obj_to_modify

    @staticmethod
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
        obj_to_modify = CmdClone.replace_common_object_attrs(
            obj_to_modify, new_obj_api_name)
        obj_to_modify.update({
            ResilientObjMap.MESSAGE_DESTINATIONS: new_obj_api_name
        })
        return obj_to_modify
