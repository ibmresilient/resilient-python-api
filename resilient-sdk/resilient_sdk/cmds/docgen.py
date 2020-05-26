#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implemention of 'resilient-sdk docgen' """

import logging
import os
import re
import pkg_resources
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util.resilient_objects import IGNORED_INCIDENT_FIELDS, ResilientObjMap

# Get the same logger object that is used in app.py
LOG = logging.getLogger("resilient_sdk_log")

# JINJA Constants
USER_GUIDE_TEMPLATE_NAME = "user_guide_README.md.jinja2"
INSTALL_GUIDE_TEMPLATE_NAME = "install_guide_README.md.jinja2"

# Relative paths from with the package of files + directories used
PATH_SETUP_PY = "setup.py"
PATH_CUSTOMIZE_PY = os.path.join("util", "customize.py")
PATH_CONFIG_PY = os.path.join("util", "config.py")
PATH_DOC_DIR = "doc"
PATH_SCREENSHOTS = os.path.join(PATH_DOC_DIR, "screenshots")
PATH_INSTALL_GUIDE_README = "README.md"
PATH_DEFAULT_INSTALL_GUIDE_README = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/README.md.jinja2")
PATH_USER_GUIDE_README = os.path.join(PATH_DOC_DIR, "README.md")
PATH_DEFAULT_USER_GUIDE_README = pkg_resources.resource_filename("resilient_sdk", "data/codegen/templates/package_template/doc/README.md.jinja2")

# Regex for splitting version number at end of name from package basename.
VERSION_REGEX = "-(\d+\.)(\d+\.)(\d+)$"

class CmdDocgen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "docgen"
    CMD_HELP = "Generate documentation for an app"
    CMD_USAGE = """
    $ resilient-sdk docgen -p <path_to_package>
    $ resilient-sdk docgen -p <path_to_package> --user-guide
    $ resilient-sdk docgen -p <path_to_package> --install-guide"""
    CMD_DESCRIPTION = CMD_HELP

    def setup(self):
        # Define docgen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p",
                                 type=ensure_unicode,
                                 help="Path to the package containing the setup.py file",
                                 nargs="?",
                                 default=os.getcwd())

        parser_group = self.parser.add_mutually_exclusive_group(required=False)

        parser_group.add_argument("--user-guide", "--uguide",
                                  help="Only generate the User Guide",
                                  action="store_true")

        parser_group.add_argument("--install-guide", "--iguide",
                                  help="Only generate the Install Guide",
                                  action="store_true")

    @staticmethod
    def _get_fn_input_details(function):
        """Return a List of all Function Inputs which are Dictionaries with
        the attributes: api_name, name, type, required, placeholder and tooltip"""

        fn_inputs = []

        for i in function.get("inputs", []):
            the_input = {}

            the_input["api_name"] = i.get("name")
            the_input["name"] = i.get("text")
            the_input["type"] = i.get("input_type")
            the_input["required"] = "Yes" if "always" in i.get("required", "") else "No"
            the_input["placeholder"] = i.get("placeholder") if i.get("placeholder") else "-"
            the_input["tooltip"] = i.get("tooltip") if i.get("tooltip") else "-"

            fn_inputs.append(the_input)

        fn_inputs = sorted(fn_inputs, key=lambda i: i["api_name"])

        return fn_inputs

    @classmethod
    def _get_function_details(cls, functions, workflows):
        """Return a List of Functions which are Dictionaries with
        the attributes: name, anchor, description, uuid, inputs,
        workflows, pre_processing_script, post_processing_script"""

        return_list = []

        for fn in functions:
            the_function = {}

            the_function["name"] = fn.get("display_name")
            the_function["anchor"] = sdk_helpers.generate_anchor(the_function.get("name"))
            the_function["description"] = fn.get("description")["content"]
            the_function["uuid"] = fn.get("uuid")
            the_function["inputs"] = cls._get_fn_input_details(fn)
            the_function["message_destination"] = fn.get("destination_handle", "")
            the_function["workflows"] = fn.get("workflows", [])

            scripts_found = False
            pre_script = None
            post_script = None

            # Loop the Function's associated Workflows
            for fn_wf in the_function.get("workflows"):

                fn_wf_name = fn_wf.get(ResilientObjMap.WORKFLOWS)

                # Loop all Workflow Objects
                for wf in workflows:

                    # Find a match
                    if fn_wf_name == wf.get(ResilientObjMap.WORKFLOWS):

                        # Get List of Function details from Workflow XML
                        workflow_functions = sdk_helpers.get_workflow_functions(wf, the_function.get("uuid"))

                        # Get a valid pre and post process script, then break
                        for a_fn in workflow_functions:

                            if not pre_script:
                                pre_script = a_fn.get("pre_processing_script")

                            if not post_script:
                                post_script = a_fn.get("post_processing_script")

                            if pre_script and post_script:
                                scripts_found = True
                                break

                    if scripts_found:
                        break

                if scripts_found:
                    break

            the_function["pre_processing_script"] = pre_script
            the_function["post_processing_script"] = post_script

            return_list.append(the_function)

        return return_list

    @staticmethod
    def _get_rule_details(rules):
        """Return a List of all Rules which are Dictionaries with
        the attributes: name, object_type and workflow_triggered"""

        return_list = []

        for rule in rules:
            the_rule = {}

            the_rule["name"] = rule.get("name")
            the_rule["object_type"] = rule.get("object_type", "")

            rule_workflows = rule.get("workflows", [])
            the_rule["workflow_triggered"] = rule_workflows[0] if rule_workflows else "-"

            return_list.append(the_rule)

        return return_list

    @staticmethod
    def _get_datatable_details(datatables):
        """Return a List of all Data Tables which are Dictionaries with
        the attributes: name, anchor, api_name, and columns. Columns is
        also a List of Dictionaries that has the attributes: name,
        api_name, type and tooltip"""

        return_list = []

        for datatable in datatables:
            the_dt = {}

            the_dt["name"] = datatable.get("display_name")
            the_dt["anchor"] = sdk_helpers.generate_anchor(the_dt.get("name"))
            the_dt["api_name"] = datatable.get("type_name")

            the_dt_columns = []

            # datatable.fields is a Dict where its values (the columns) also Dicts
            for col in datatable.get("fields", {}).values():
                the_col = {}

                the_col["name"] = col.get("text")
                the_col["api_name"] = col.get("name")
                the_col["type"] = col.get("input_type")
                the_col["tooltip"] = col.get("tooltip") if col.get("tooltip") else "-"

                the_dt_columns.append(the_col)

            the_dt["columns"] = sorted(the_dt_columns, key=lambda c: c["api_name"])

            return_list.append(the_dt)

        return return_list

    @staticmethod
    def _get_custom_fields_details(fields):
        """Return a List of all Custom Incident Fields which are Dictionaries with
        the attributes: api_name, label, type, prefix, placeholder and tooltip"""
        return_list = []

        for field in fields:
            the_field = {}

            the_field["api_name"] = field.get("name")
            the_field["label"] = field.get("text")
            the_field["type"] = field.get("input_type")
            the_field["prefix"] = field.get("prefix")
            the_field["placeholder"] = field.get("placeholder") if field.get("placeholder") else "-"
            the_field["tooltip"] = field.get("tooltip") if field.get("tooltip") else "-"

            return_list.append(the_field)

        return return_list

    @staticmethod
    def _get_custom_artifact_details(custom_artifact_types):
        """Return a List of all Custom Incident Artifact Types which are Dictionaries with
        the attributes: api_name, display_name and description"""
        return_list = []

        for artifact_type in custom_artifact_types:
            the_artifact_type = {}

            the_artifact_type["api_name"] = artifact_type.get("programmatic_name")
            the_artifact_type["display_name"] = artifact_type.get("name")
            the_artifact_type["description"] = artifact_type.get("desc")

            return_list.append(the_artifact_type)

        return return_list

    def execute_command(self, args):
        LOG.debug("docgen called with %s", args)

        # Set docgen name for SDKException
        SDKException.command_ran = self.CMD_NAME

        # Get absolute path_to_src
        path_to_src = os.path.abspath(args.p)

        # Get basename of path_to_src (version information is stripped from the basename).
        path_to_src_basename = re.split(VERSION_REGEX, os.path.basename(path_to_src), 1)[0]

        LOG.debug("Path to project: %s", path_to_src)
        LOG.debug("Project basename: %s", path_to_src_basename)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env("data/docgen/templates")

        # Load the Jinja2 Templates
        user_guide_readme_template = jinja_env.get_template(USER_GUIDE_TEMPLATE_NAME)
        install_guide_readme_template = jinja_env.get_template(INSTALL_GUIDE_TEMPLATE_NAME)

        # Generate paths to required directories + files
        path_setup_py_file = os.path.join(path_to_src, PATH_SETUP_PY)
        path_customize_py_file = os.path.join(path_to_src, path_to_src_basename, PATH_CUSTOMIZE_PY)
        path_config_py_file = os.path.join(path_to_src, path_to_src_basename, PATH_CONFIG_PY)
        path_install_guide_readme = os.path.join(path_to_src, PATH_INSTALL_GUIDE_README)
        path_doc_dir = os.path.join(path_to_src, PATH_DOC_DIR)
        path_screenshots_dir = os.path.join(path_to_src, PATH_SCREENSHOTS)
        path_user_guide_readme = os.path.join(path_to_src, PATH_USER_GUIDE_README)

        # Ensure we have read permissions for each required file and the file exists
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file, path_customize_py_file, path_config_py_file)

        # Check doc directory exists, if not, create it
        if not os.path.isdir(path_doc_dir):
            os.makedirs(path_doc_dir)

        # Check doc/screenshots directory exists, if not, create it
        if not os.path.isdir(path_screenshots_dir):
            os.makedirs(path_screenshots_dir)

        # Set generate guide flags. Will generate both by default
        do_generate_user_guide = False if args.install_guide else True
        do_generate_install_guide = False if args.user_guide else True

        # Parse the setup.py file
        setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        # Get the resilient_circuits dependency string from setup.py file
        res_circuits_dep_str = package_helpers.get_dependency_from_install_requires(setup_py_attributes.get("install_requires"), "resilient_circuits")

        # Get ImportDefinition from customize.py
        customize_py_import_def = package_helpers.get_import_definition_from_customize_py(path_customize_py_file)

        # Parse the app.configs from the config.py file
        jinja_app_configs = package_helpers.get_configs_from_config_py(path_config_py_file)

        # Get field names from ImportDefinition
        field_names = []
        for f in customize_py_import_def.get("fields", []):
            f_name = f.get(ResilientObjMap.FIELDS, "")

            if "incident/" in f_name and f_name not in IGNORED_INCIDENT_FIELDS:
                field_names.append(f_name.split("incident/")[1])

        # Get data from ImportDefinition
        import_def_data = sdk_helpers.get_from_export(customize_py_import_def,
                                                      message_destinations=sdk_helpers.get_object_api_names(ResilientObjMap.MESSAGE_DESTINATIONS, customize_py_import_def.get("message_destinations")),
                                                      functions=sdk_helpers.get_object_api_names(ResilientObjMap.FUNCTIONS, customize_py_import_def.get("functions")),
                                                      workflows=sdk_helpers.get_object_api_names(ResilientObjMap.WORKFLOWS, customize_py_import_def.get("workflows")),
                                                      rules=sdk_helpers.get_object_api_names(ResilientObjMap.RULES, customize_py_import_def.get("actions")),
                                                      fields=field_names,
                                                      artifact_types=sdk_helpers.get_object_api_names(ResilientObjMap.INCIDENT_ARTIFACT_TYPES, customize_py_import_def.get("incident_artifact_types")),
                                                      datatables=sdk_helpers.get_object_api_names(ResilientObjMap.DATATABLES, customize_py_import_def.get("types")),
                                                      tasks=sdk_helpers.get_object_api_names(ResilientObjMap.TASKS, customize_py_import_def.get("automatic_tasks")),
                                                      scripts=sdk_helpers.get_object_api_names(ResilientObjMap.SCRIPTS, customize_py_import_def.get("scripts")))

        # Lists we use in Jinja Templates
        jinja_functions = self._get_function_details(import_def_data.get("functions", []), import_def_data.get("workflows", []))
        jinja_rules = self._get_rule_details(import_def_data.get("rules", []))
        jinja_datatables = self._get_datatable_details(import_def_data.get("datatables", []))
        jinja_custom_fields = self._get_custom_fields_details(import_def_data.get("fields", []))
        jinja_custom_artifact_types = self._get_custom_artifact_details(import_def_data.get("artifact_types", []))

        # Other variables for Jinja Templates
        package_name_underscore = setup_py_attributes.get("name", "")
        package_name_dash = package_name_underscore.replace("_", "-")
        server_version = customize_py_import_def.get("server_version", {})

        if do_generate_user_guide:

            LOG.info("Rendering User Guide for %s", package_name_dash)

            # Render the User Guide Jinja2 Templeate with parameters
            rendered_user_guide_readme = user_guide_readme_template.render({
                "name": package_name_underscore,
                "version": setup_py_attributes.get("version"),
                "functions": jinja_functions,
                "rules": jinja_rules,
                "datatables": jinja_datatables,
                "custom_fields": jinja_custom_fields,
                "custom_artifact_types": jinja_custom_artifact_types,
                "name_underscore": package_name_underscore
            })

            # Create a backup if needed of user guide README
            sdk_helpers.rename_to_bak_file(path_user_guide_readme, PATH_DEFAULT_USER_GUIDE_README)

            LOG.info("Writing User Guide to: %s", path_user_guide_readme)

            # Write the new User Guide README
            sdk_helpers.write_file(path_user_guide_readme, rendered_user_guide_readme)

        if do_generate_install_guide:
            LOG.info("Rendering Install Guide")

            # Render the Install Guide Jinja2 Templeate with parameters
            rendered_install_guide_readme = install_guide_readme_template.render({
                "short_description": setup_py_attributes.get("description"),
                "long_description": setup_py_attributes.get("long_description"),
                "name_underscore": package_name_underscore,
                "name_dash": package_name_dash,
                "server_version": server_version.get("version"),
                "res_circuits_dependency_str": res_circuits_dep_str,
                "app_configs": jinja_app_configs[1],
                "version": setup_py_attributes.get("version"),
                "author": setup_py_attributes.get("author"),
                "support_url": setup_py_attributes.get("url"),
                "datatables": jinja_datatables,
                "custom_incident_fields": jinja_custom_fields
            })

            # Create a backup if needed of install guide README
            sdk_helpers.rename_to_bak_file(path_install_guide_readme, PATH_DEFAULT_INSTALL_GUIDE_README)

            LOG.info("Writing Install Guide to: %s", path_install_guide_readme)

            # Write the new Install Guide README
            sdk_helpers.write_file(path_install_guide_readme, rendered_install_guide_readme)
