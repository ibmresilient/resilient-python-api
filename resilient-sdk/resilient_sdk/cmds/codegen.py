#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" Implementation of `resilient-sdk codegen` """

import logging
import os
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.helpers import (get_resilient_client, setup_jinja_env,
                                        is_valid_package_name, write_file,
                                        validate_dir_paths, get_latest_org_export,
                                        get_from_export, minify_export,
                                        get_object_api_names)

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")


class CmdCodegen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "codegen"
    CMD_HELP = "Generate boilerplate code to start developing an Extension"
    CMD_USAGE = "resilient-sdk codegen -p <name_of_package> -m <message_destination>"
    CMD_DESCRIPTION = "Generate boilerplate code to start developing an Extension"
    CMD_USE_COMMON_PARSER_ARGS = True

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="Name of the package to generate")

        self.parser.add_argument("--reload",
                                 action="store_true",
                                 help="Reload customizations and create new customize.py")

    def execute_command(self, args):
        LOG.info("Called codegen command")

        # Set command name in our SDKException class
        SDKException.command_ran = self.CMD_NAME

        # Instansiate connection to the Resilient Appliance
        res_client = get_resilient_client()

        if args.reload:
            self._reload_package(res_client, args)

        elif args.package:
            self._gen_package(res_client, args)

        elif not args.package and args.function:
            self._gen_function(res_client, args)

        else:
            self.parser.print_help()

    @staticmethod
    def render_jinja_mapping(jinja_mapping_dict, jinja_env, target_dir):
        """
        Write all the Jinja Templates specified in jinja_mapping_dict that
        are found in the jinja_env to the target_dir

        :param jinja_mapping_dict: e.g. {"file_to_write.py": ("name_of_template.py.jinja2", jinja_data)}
        :param jinja_env: Jinja Environment
        :param target_dir: Path to write Templates to
        """
        for (file_name, file_info) in jinja_mapping_dict.items():

            if isinstance(file_info, dict):
                # This is a sub directory
                sub_dir_mapping_dict = file_info
                path_sub_dir = os.path.join(target_dir, file_name)

                try:
                    os.makedirs(path_sub_dir)
                except OSError as err_msg:
                    LOG.warn(err_msg)

                CmdCodegen.render_jinja_mapping(sub_dir_mapping_dict, jinja_env, path_sub_dir)

            else:
                # Get path to Jinja2 template
                path_template = file_info[0]

                # Get data dict for this Jinja2 template
                template_data = file_info[1]

                target_file = os.path.join(target_dir, file_name)

                if os.path.exists(target_file):
                    LOG.warning(u"File already exists. Not writing: %s", target_file)
                    continue

                jinja_template = jinja_env.get_template(path_template)
                jinja_rendered_text = jinja_template.render(template_data)

                write_file(target_file, jinja_rendered_text)

    @staticmethod
    def _gen_function(res_client, args):
        # TODO: Handle just generating a FunctionComponent for the /components directory
        LOG.info("codegen _gen_function called")

    @staticmethod
    def _gen_package(res_client, args):
        LOG.info("codegen _gen_package called")

        if not is_valid_package_name(args.package):
            raise SDKException(u"'{0}' is not a valid package name".format(args.package))

        package_name = args.package

        # Get output_base, use args.output if defined, else current directory
        output_base = args.output if args.output else os.curdir
        output_base = os.path.abspath(output_base)

        # TODO: handle being passed path to an actual export.res file
        org_export = get_latest_org_export(res_client)

        # Get data required for Jinja2 templates from export
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
        jinja_data["export_data"] = minify_export(org_export,
                                                  message_destinations=get_object_api_names("x_api_name", jinja_data.get("message_destinations")),
                                                  functions=get_object_api_names("x_api_name", jinja_data.get("functions")),
                                                  workflows=get_object_api_names("x_api_name", jinja_data.get("workflows")),
                                                  rules=get_object_api_names("x_api_name", jinja_data.get("rules")),
                                                  fields=jinja_data.get("all_fields"),
                                                  artifact_types=get_object_api_names("x_api_name", jinja_data.get("artifact_types")),
                                                  datatables=get_object_api_names("x_api_name", jinja_data.get("datatables")),
                                                  tasks=get_object_api_names("x_api_name", jinja_data.get("tasks")),
                                                  phases=get_object_api_names("x_api_name", jinja_data.get("phases")),
                                                  scripts=get_object_api_names("x_api_name", jinja_data.get("scripts")))

        # Add package_name to jinja_data
        jinja_data["package_name"] = package_name

        # Validate we have write permissions
        validate_dir_paths(os.W_OK, output_base)

        # Join package_name to output base
        output_base = os.path.join(output_base, package_name)

        # If the output_base directory does not exist, create it
        if not os.path.exists(output_base):
            os.makedirs(output_base)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = setup_jinja_env("data/codegen/templates/package_template")

        # This dict maps our package file structure to  Jinja2 templates
        package_mapping_dict = {
            "MANIFEST.in": ("MANIFEST.in.jinja2", jinja_data),
            "README.md": ("README.md.jinja2", jinja_data),
            "setup.py": ("setup.py.jinja2", jinja_data),
            "tox.ini": ("tox.ini.jinja2", jinja_data),

            package_name: {
                "__init__.py": ("package/__init__.py.jinja2", jinja_data),
                "LICENSE": ("package/LICENSE.jinja2", jinja_data),

                "components": {
                    "__init__.py": ("package/components/__init__.py.jinja2", jinja_data),
                },
                "util": {
                    "__init__.py": ("package/util/__init__.py.jinja2", jinja_data),
                    "config.py": ("package/util/config.py.jinja2", jinja_data),
                    "customize.py": ("package/util/customize.py.jinja2", jinja_data),
                    "selftest.py": ("package/util/selftest.py.jinja2", jinja_data),
                }
            }
        }

        # If there are Functions, add a 'tests' directory
        if jinja_data.get("functions"):
            package_mapping_dict["tests"] = {}

        # Loop each Function
        for f in jinja_data.get("functions"):
            # Add package_name to function data
            f["package_name"] = package_name

            # Generate function_component.py file name
            file_name = u"funct_{0}.py".format(f.get("export_key"))

            # Add to 'components' directory
            package_mapping_dict[package_name]["components"][file_name] = ("package/components/function.py.jinja2", f)

            # Add to 'tests' directory
            package_mapping_dict["tests"][u"test_{0}".format(file_name)] = ("tests/test_function.py.jinja2", f)

        CmdCodegen.render_jinja_mapping(package_mapping_dict, jinja_env, output_base)

    @staticmethod
    def _reload_package(res_client, args):
        # TODO: Implement 'resilient-sdk codegen --reload'
        LOG.info("codegen _reload_package called")
