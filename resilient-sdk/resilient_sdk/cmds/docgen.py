#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implemention of 'resilient-sdk docgen' """

import logging
import os
import shutil
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util.resilient_objects import IGNORED_INCIDENT_FIELDS, ResilientObjMap

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)

# JINJA Constants
README_TEMPLATE_NAME = "README.md.jinja2"


class CmdDocgen(BaseCmd):
    """
    Create a README.md for the specified app. Reads all details from
    the ImportDefinition in the customize.py file. Creates a backup of
    of the README.md if one exists already. The README.md is
    really an 'inventory' of what the app contains and details for
    the app configs
    """

    CMD_NAME = "docgen"
    CMD_HELP = "Generate documentation for an app"
    CMD_USAGE = """
    $ resilient-sdk docgen -p <path_to_package>"""
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
        the attributes: name, simple_name, anchor, description, uuid, inputs,
        workflows, pre_processing_script, post_processing_script"""

        return_list = []

        for fn in functions:
            the_function = {}

            the_function["name"] = fn.get("display_name")
            the_function["simple_name"] = sdk_helpers.simplify_string(the_function.get("name"))
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
    def _get_script_details(scripts):
        """Return a List of all Scripts which are Dictionaries with
        the attributes: name, simple_name, description, object_type, script_text"""

        return_list = []

        for s in scripts:
            the_script = {}

            the_script["name"] = s.get("name")
            the_script["simple_name"] = sdk_helpers.simplify_string(the_script.get("name"))
            the_script["anchor"] = sdk_helpers.generate_anchor(the_script.get("name"))
            the_script["description"] = s.get("description")
            the_script["object_type"] = s.get("object_type")
            the_script["script_text"] = s.get("script_text")
            return_list.append(the_script)

        return return_list

    @staticmethod
    def _get_rule_details(rules):
        """Return a List of all Rules which are Dictionaries with
        the attributes: name, simple_name, object_type and workflow_triggered"""

        return_list = []

        for rule in rules:
            the_rule = {}

            the_rule["name"] = rule.get("name")
            the_rule["simple_name"] = sdk_helpers.simplify_string(the_rule.get("name"))
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
            the_dt["simple_name"] = sdk_helpers.simplify_string(the_dt.get("name"))
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

        LOG.debug("Path to project: %s", path_to_src)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env("data/docgen/templates")

        # Load the Jinja2 Templates
        readme_template = jinja_env.get_template(README_TEMPLATE_NAME)

        # Generate path to setup.py file
        path_setup_py_file = os.path.join(path_to_src, package_helpers.PATH_SETUP_PY)

        try:
            # Ensure we have read permissions for setup.py
            sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)
        except SDKException as err:
            err.message += "\nEnsure you are in the directory of the package you want to run docgen for"
            raise err

        # Parse the setup.py file
        setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        package_name = setup_py_attributes.get("name", "")

        # Generate paths to other required directories + files
        path_customize_py_file = os.path.join(path_to_src, package_name, package_helpers.PATH_CUSTOMIZE_PY)
        path_config_py_file = os.path.join(path_to_src, package_name, package_helpers.PATH_CONFIG_PY)
        path_readme = os.path.join(path_to_src, package_helpers.PATH_README)
        path_screenshots_dir = os.path.join(path_to_src, package_helpers.PATH_SCREENSHOTS)

        # Ensure we have read permissions for each required file and the file exists
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file, path_customize_py_file, path_config_py_file)

        # Check doc/screenshots directory exists, if not, create it + copy default screenshot
        if not os.path.isdir(path_screenshots_dir):
            os.makedirs(path_screenshots_dir)
            shutil.copy(package_helpers.PATH_DEFAULT_SCREENSHOT, path_screenshots_dir)

        # Get the resilient_circuits dependency string from setup.py file
        res_circuits_dep_str = package_helpers.get_dependency_from_install_requires(setup_py_attributes.get("install_requires"), "resilient_circuits")

        # Get ImportDefinition from customize.py
        customize_py_import_def = package_helpers.get_import_definition_from_customize_py(path_customize_py_file)

        # Parse the app.configs from the config.py file
        jinja_app_configs = package_helpers.get_configs_from_config_py(path_config_py_file)

        # Get field names from ImportDefinition
        field_names = []
        for f in customize_py_import_def.get("fields", []):
            f_export_key = f.get("export_key")

            if "incident/" in f_export_key and f_export_key not in IGNORED_INCIDENT_FIELDS:
                field_names.append(f.get(ResilientObjMap.FIELDS, ""))

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
        jinja_scripts = self._get_script_details(import_def_data.get("scripts", []))
        jinja_rules = self._get_rule_details(import_def_data.get("rules", []))
        jinja_datatables = self._get_datatable_details(import_def_data.get("datatables", []))
        jinja_custom_fields = self._get_custom_fields_details(import_def_data.get("fields", []))
        jinja_custom_artifact_types = self._get_custom_artifact_details(import_def_data.get("artifact_types", []))

        # Other variables for Jinja Templates
        package_name_dash = package_name.replace("_", "-")
        server_version = customize_py_import_def.get("server_version", {})
        supported_app = sdk_helpers.does_url_contain(setup_py_attributes.get("url", ""), "ibm.com/mysupport")

        LOG.info("Rendering README for %s", package_name_dash)

        # Render the README Jinja2 Templeate with parameters
        rendered_readme = readme_template.render({
            "name_underscore": package_name,
            "name_dash": package_name_dash,
            "display_name": setup_py_attributes.get("display_name", package_name),
            "short_description": setup_py_attributes.get("description"),
            "long_description": setup_py_attributes.get("long_description"),
            "version": setup_py_attributes.get("version"),
            "server_version": server_version.get("version"),
            "res_circuits_dependency_str": res_circuits_dep_str,
            "author": setup_py_attributes.get("author"),
            "support_url": setup_py_attributes.get("url"),
            "supported_app": supported_app,
            "app_configs": jinja_app_configs[1],
            "functions": jinja_functions,
            "scripts": jinja_scripts,
            "rules": jinja_rules,
            "datatables": jinja_datatables,
            "custom_fields": jinja_custom_fields,
            "custom_artifact_types": jinja_custom_artifact_types
        })

        # Create a backup if needed of README
        sdk_helpers.rename_to_bak_file(path_readme, package_helpers.PATH_DEFAULT_README)

        LOG.info("Writing README to: %s", path_readme)

        # Write the new README
        sdk_helpers.write_file(path_readme, rendered_readme)
