#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of 'resilient-sdk extract' """

import os
import sys
import json
import logging
import shutil
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util import sdk_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)


class CmdExtract(BaseCmd):
    """
    resilient-sdk extract allows you to 'extract' Resilient Objects
    from a Resilient Export

    It will create a Resilient Export file (.res) of the specified Resilient Objects

    If passed the --zip parameter, it will create a .zip containing the .res file
    """

    CMD_NAME = "extract"
    CMD_HELP = "Extract data in order to publish a .res file"
    CMD_USAGE = """
    $ resilient-sdk extract -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
    $ resilient-sdk extract --script 'custom_script' --zip
    $ resilient-sdk extract --script 'custom_script' --name 'my_custom_export'"""
    CMD_DESCRIPTION = "Extract data in order to publish a .res export file"
    CMD_ADD_PARSERS = ["res_obj_parser", "io_parser", "zip_parser"]

    def setup(self):
        # Define docgen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any optional arguments here
        self.parser.add_argument("-n", "--name",
                                 type=ensure_unicode,
                                 help="Name to prepend to generated file",
                                 nargs="?")

    def execute_command(self, args):
        LOG.info("Starting 'extract'...")
        LOG.debug("'extract' called with %s", args)

        # Set docgen name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get output_base, use args.output if defined, else current directory
        output_base = args.output if args.output else os.curdir
        output_base = os.path.abspath(output_base)

        # If --exportfile is specified, read org_export from that file
        if args.exportfile:
            LOG.info("Using local export file: %s", args.exportfile)
            org_export = sdk_helpers.read_local_exportfile(args.exportfile)

        else:
            # Instantiate connection to the Resilient Appliance
            res_client = sdk_helpers.get_resilient_client()

            # Generate + get latest export from Resilient Server
            org_export = sdk_helpers.get_latest_org_export(res_client)

        LOG.info("Extracting data from export...")

        # Get extracted data from export
        extract_data = sdk_helpers.get_from_export(org_export,
                                                   message_destinations=args.messagedestination,
                                                   functions=args.function,
                                                   workflows=args.workflow,
                                                   rules=args.rule,
                                                   fields=args.field,
                                                   artifact_types=args.artifacttype,
                                                   datatables=args.datatable,
                                                   tasks=args.task,
                                                   scripts=args.script)

        # Get 'minified' version of the export. This is used in to create export.res
        min_extract_data = sdk_helpers.minify_export(org_export,
                                                     message_destinations=sdk_helpers.get_object_api_names(ResilientObjMap.MESSAGE_DESTINATIONS, extract_data.get("message_destinations")),
                                                     functions=sdk_helpers.get_object_api_names(ResilientObjMap.FUNCTIONS, extract_data.get("functions")),
                                                     workflows=sdk_helpers.get_object_api_names(ResilientObjMap.WORKFLOWS, extract_data.get("workflows")),
                                                     rules=sdk_helpers.get_object_api_names(ResilientObjMap.RULES, extract_data.get("rules")),
                                                     fields=extract_data.get("all_fields"),
                                                     artifact_types=sdk_helpers.get_object_api_names(ResilientObjMap.INCIDENT_ARTIFACT_TYPES, extract_data.get("artifact_types")),
                                                     datatables=sdk_helpers.get_object_api_names(ResilientObjMap.DATATABLES, extract_data.get("datatables")),
                                                     tasks=sdk_helpers.get_object_api_names(ResilientObjMap.TASKS, extract_data.get("tasks")),
                                                     phases=sdk_helpers.get_object_api_names(ResilientObjMap.PHASES, extract_data.get("phases")),
                                                     scripts=sdk_helpers.get_object_api_names(ResilientObjMap.SCRIPTS, extract_data.get("scripts")))

        # Convert dict to JSON string
        if sys.version_info.major >= 3:
            res_data = json.dumps(min_extract_data, ensure_ascii=False)
        else:
            res_data = unicode(json.dumps(min_extract_data, ensure_ascii=False))

        # Generate path to file
        file_name = "export-{0}".format(sdk_helpers.get_timestamp(org_export.get("export_date", 0) / 1000.0))

        # If custom name supplied, prepend it
        if args.name:
            file_name = "{0}-{1}".format(args.name, file_name)

        path_file_to_write = os.path.join(output_base, "{0}.res".format(file_name))

        LOG.info("Generating %s.res", file_name)

        # Write the file
        sdk_helpers.write_file(path_file_to_write, res_data)

        LOG.debug('Wrote: %s', path_file_to_write)

        # If we should create .zip archive
        if args.zip:

            LOG.info("Generating %s.zip", file_name)

            # Get path to .zip
            path_dir_to_zip = os.path.join(output_base, file_name)

            # Create directory
            os.makedirs(path_dir_to_zip)

            # Copy the written export file into new dir
            shutil.copy(path_file_to_write, path_dir_to_zip)

            # zip the dir
            the_zip = shutil.make_archive(base_name=file_name, format="zip", root_dir=path_dir_to_zip)

            if output_base != os.path.dirname(the_zip):
                # Move the zip into the output base
                shutil.move(the_zip, output_base)

            LOG.debug('Wrote: %s.zip', path_dir_to_zip)

            # Remove directory
            shutil.rmtree(path_dir_to_zip)

        LOG.info("'extract' complete")
