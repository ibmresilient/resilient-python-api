#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

""" Implementation of 'resilient-sdk list' """

import logging
import re

from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.cmds import CmdCodegen
from resilient_sdk.util import constants, sdk_helpers, package_file_helpers
from resilient_sdk.util.resilient_objects import (ResilientObjMap,
                                                  ResilientTypeIds)
from resilient_sdk.util.sdk_exception import SDKException

from resilient import ensure_unicode

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)
TAB_SEP = "   " # use 4 spaces here rather than "\t" because "\t" is too big

MAPPING_TUPLES = [
    # tuple schema:
    # <Display Name>, <cmd line arg name>, <export api name>, <ResilientObjMap>, <is API name?>, <condition function to retrieve objects that are nested in other object>
    ("Message Destinations", "messagedestination", "message_destinations", ResilientObjMap.MESSAGE_DESTINATIONS, True, None),
    ("Functions", "function", "functions", ResilientObjMap.FUNCTIONS, True, None),
    ("Workflows", "workflow", "workflows", ResilientObjMap.WORKFLOWS, True, None),
    ("Rules", "rule", "actions", ResilientObjMap.RULES, False, None),
    ("Incident Fields", "field", "fields", ResilientObjMap.FIELDS, True, lambda o: True if o.get("type_id") == ResilientTypeIds.INCIDENT else False),
    ("Artifact Types", "artifacttype", "incident_artifact_types", ResilientObjMap.INCIDENT_ARTIFACT_TYPES, False, None),
    ("Incident Types", "incidenttype", "incident_types", ResilientObjMap.INCIDENT_TYPES, False, None),
    ("Datatables", "datatable", "types", ResilientObjMap.DATATABLES, True, lambda o: True if o.get("type_id") == ResilientTypeIds.DATATABLE else False),
    ("Tasks", "task", "automatic_tasks", ResilientObjMap.TASKS, True, None),
    ("Scripts", "script", "scripts", ResilientObjMap.SCRIPTS, False, None),
    ("Playbooks", "playbook", "playbooks", ResilientObjMap.PLAYBOOKS, True, None)
]

class CmdList(BaseCmd):
    """
    List the available objects from the connected SOAR instance or export file
    """

    CMD_NAME = "list"
    CMD_HELP = "Lists available objects from SOAR."
    CMD_DESCRIPTION = "List available objects from SOAR. For each of the objects below, either leave blank to list all, provide a prefix string to filter by prefix, or provide a regex to filter matching object names."
    CMD_USAGE = """
    $ resilient-sdk list --function                           # list all functions
    $ resilient-sdk list --function "fn_my_app.*" --playbook  # list all functions that start with fn_my_app and all playbooks
    $ resilient-sdk list --global-filter ".*(?i)cyber.*"      # matches all objects with "cyber" in them (uses '(?i)' for case-insensitive)
    $ resilient-sdk list --function --codegen-format          # list all functions and give output in codegen format
    """
    CMD_ADD_PARSERS = [constants.APP_CONFIG_PARSER_NAME, constants.RESILIENT_OBJECTS_PARSER_NAME]

    def setup(self):
        SDKException.command_ran = self.CMD_NAME

        # Define list usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        self.parser.add_argument("-g", "--global-filter",
                                 type=ensure_unicode,
                                 help="Regex to filter on all objects. If a specific object filter is provided it overrides the --global-filter filter",
                                 nargs="+")

        self.parser.add_argument("-e", "--exportfile",
                                 type=ensure_unicode,
                                 help="Path to a local (.res or .resz) export file")

        self.parser.add_argument("-cf", "--codegen-format",
                                 action="store_true",
                                 help="Output results in codegen-friendly format")

    def execute_command(self, args):
        """
        Run ``list`` command
        """

        LOG.debug("called: CmdList.execute_command()")
        SDKException.command_ran = self.CMD_NAME

        if args.exportfile:
            LOG.info("Using local export file: %s", args.exportfile)
            org_export = sdk_helpers.read_local_exportfile(args.exportfile)
        else:
            # Instantiate connection to SOAR and create/download latest full export
            res_client = sdk_helpers.get_resilient_client(path_config_file=args.config)
            org_export = sdk_helpers.get_latest_org_export(res_client)

        results = {}
        LOG.debug("%sListing objects%s", constants.LOG_DIVIDER, constants.LOG_DIVIDER)
        for arg_display_name, arg_key, export_key, obj_api_name_map, is_api_name, condition in MAPPING_TUPLES:
            # if all objects was passed, place same filter on all objects
            if args.global_filter and getattr(args, arg_key) is None:
                setattr(args, arg_key, args.global_filter)

            # get filters (might be set by the global filter -g/--global-filter)
            filters = getattr(args, arg_key)
            object_list = org_export.get(export_key)

            # check if the object was requested in the args
            if filters is not None:
                results[arg_key] = {
                    "name_list": CmdList.list_objects(obj_api_name_map, object_list, arg_key, filters=filters, condition=condition),
                    "arg_key": arg_key,
                    "arg_display_name": arg_display_name,
                    "is_api_name": is_api_name,
                    "filters": filters
                }
            else:
                LOG.debug("Skipping %s. Add '--%s' to list command to include", arg_display_name, arg_key)

        if args.codegen_format:
            CmdList._print_results_codegen_format(results)
        else:
            CmdList._print_results_to_console(results)

    @staticmethod
    def list_objects(object_api_name, object_list, arg_key, filters=None, condition=None):
        """
        Get a list of the object names available given the filters and conditions set.
        Return the list sorted alphabetically, ignoring case

        ``object_list`` is generally acquired from the org export by ``org_export.get(export_key)``

        Ex:

        .. code-block::python

            object_list = org_export.get("functions")
            CmdList.list_objects(ResilientObjMap.FUNCTIONS, object_list, "function", filters=".*")

        :param object_api_name: ResilientObjMap value for the object
        :type object_api_name: str
        :param object_list: list of dictionaries of the details of the object
        :type object_list: list[dict]
        :param arg_key: object key name from cmd line arg
        :type arg_key: str
        :param filters: list of regex filters to pass to CmdList._apply_regex_filters, defaults to None
        :type filters: list[str], optional
        :param condition: condition to run against the object_list list if the object lives as a subset of another object (ex: datatables), defaults to None
        :type condition: func or lambda, optional
        """
        # use condition function to filter in special cases, otherwise just pull export_key from export
        object_list = [o for o in object_list if condition(o)] if condition else object_list

        # map objects to list of object API (or reference if applicable) names
        export_obj_names = sdk_helpers.get_object_api_names(object_api_name, object_list)

        # apply list of regex filters to the names retrieved
        LOG.debug("Applying filter(s) to '%s'", arg_key)
        results = CmdList._apply_regex_filters(export_obj_names, filters=filters)

        return sorted(results, key=lambda x: x.lower()) # return sorted ignoring case

    @staticmethod
    def _apply_regex_filters(export_obj_names, filters=None):
        """
        Given a list of names, filter out those that don't match any
        of the given list of regex conditions

        :param export_obj_names: list of names
        :type export_obj_names: list[str]
        :param filters: regex string or list of regex strings to filter the names by, defaults to None
        :type filters: str | list[str], optional
        :raises SDKException: raises SDKException if a regex exception occurs
        :return: filtered list of names with any that don't match any regex given
        :rtype: list[str]
        """
        filtered_names = []

        # if no filter provided return original list
        if not filters:
            LOG.debug("%sNo regex filters provided; returning full list", TAB_SEP)
            return export_obj_names

        # potential use case passes just one regex string in here (like ".*")
        # (though no possible through cmdline exec)
        # so to handle this properly, we convert to a list containing the one str
        if isinstance(filters, str):
            LOG.debug("%sFilter provided is a string, not list: %s.\nConsider passing a list of filters to CmdList._apply_regex_filters", TAB_SEP, filters)
            filters = [filters]

        for re_filter in filters:
            try:
                filtered_names.extend([o for o in export_obj_names if re.match(re_filter, o)])
                LOG.debug("%sSuccessfully applied filter '%s'", TAB_SEP, re_filter)
            except re.error as exc:
                raise SDKException("Regex {0} failed to properly parse. Please ensure it is correct. Details: {1}".format(re_filter, exc))

        return filtered_names

    @staticmethod
    def _print_results_to_console(results):
        """
        Print results in a pretty, human-readable format.

        :param results: result dict containing (at least) "name_list" (list of the names),
                        "arg_display_name" (Display name to label section with),
                        and "filters" (optional list of filters)
        :type results: dict
        """
        LOG.debug("Logging results in pretty format to console. Use -cf/--codegen-format to log in codegen specific format")
        LOG.info("%sList results:%s", constants.LOG_DIVIDER, constants.LOG_DIVIDER)

        # sort empty lists to the top
        for key in sorted(results, key=lambda x: results.get(x).get("name_list")):
            result = results[key]

            arg_name = result.get("arg_display_name")
            filters = result.get("filters", [])
            name_list = result.get("name_list")

            if name_list:
                # log the results in a pretty format
                LOG.info("%s:", arg_name)
                joined_names = "\n{0}- ".format(TAB_SEP).join(name_list)
                LOG.info("%s- %s", TAB_SEP, joined_names)
            else:
                # if filters were used, include them in the message
                if filters and isinstance(filters, list):
                    filter_list = ["'{0}'".format(f) for f in filters]
                    LOG.info("No %s matching filter %s in this export", arg_name, " or ".join(filter_list))
                else:
                    LOG.info("No %s in this export", arg_name)

    @staticmethod
    def _print_results_codegen_format(results):
        """
        Print results in a format that can be easily copied and used with codegen.

        Example:

            --messagedestination fn_test_md --function fn_test_func

        :param results: result dict containing (at least) "name_list" (list of the names),
                        "arg_key" (API/display name used in codegen), and "is_api_name" (T/F)
        :type results: dict
        """
        LOG.info("%sList results in codegen format:%s", constants.LOG_DIVIDER, constants.LOG_DIVIDER)

        outputs = []
        # list through results (each result is a SOAR object) and build out their output strings
        for key in results:
            result = results[key]

            # get name_list, filters, and arg_key from result dict
            name_list = result.get("name_list")
            filters = result.get("filters", [])
            arg_key = result.get("arg_key")

            # check to make sure results were found
            # if no results found, debug log and gracefully move on
            # if results were found, then format the results for codegen
            # and append to the list of outputs which will be logged at the end
            if name_list:
                # if not an API name, then define wrapper char as \"
                is_api_name = result.get("is_api_name")
                wrapper_char = "\"" if not is_api_name else ""

                # join names and color them yellow for easier reading in the console
                joined_names = package_file_helpers.color_output(" ".join(["{0}{1}{0}".format(wrapper_char, r) for r in name_list]), "YELLOW")
                outputs.append("--{0} {1}".format(arg_key, joined_names))
            else:
                # if filters were used, include them in the message
                if filters and isinstance(filters, list):
                    filter_list = ["'{0}'".format(f) for f in filters]
                    LOG.debug("No %s matching filter %s in this export", result.get("arg_display_name"), ", ".join(filter_list))
                else:
                    LOG.debug("No %s in this export", result.get("arg_display_name"))

        output_str = " ".join(outputs)
        LOG.info("%s %s %s -p <path_to_package>", constants.SDK_PACKAGE_NAME, CmdCodegen.CMD_NAME, output_str)
