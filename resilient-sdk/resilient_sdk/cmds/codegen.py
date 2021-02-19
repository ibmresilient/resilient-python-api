#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

""" Implementation of `resilient-sdk codegen` """

import logging
import os
import shutil
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)


class CmdCodegen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "codegen"
    CMD_HELP = "Generate boilerplate code to start developing an app"
    CMD_USAGE = """
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two'
    $ resilient-sdk codegen -p <path_current_package> --reload --workflow 'new_wf_to_add'"""
    CMD_DESCRIPTION = CMD_HELP
    CMD_ADD_PARSERS = ["res_obj_parser", "io_parser"]

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument("-p", "--package",
                                 type=ensure_unicode,
                                 help="(required) Name of new or path to existing package")

        self.parser.add_argument("-re", "--reload",
                                 action="store_true",
                                 help="Reload customizations and create new customize.py")

    def execute_command(self, args):
        LOG.debug("called: CmdCodegen.execute_command()")

        if args.reload:
            if not args.package:
                raise SDKException("'-p' must be specified when using '--reload'")

            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, "--reload")
            self._reload_package(args)

        elif args.package:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, "--package | -p")
            self._gen_package(args)

        elif not args.package and args.function:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, "--function | -f")
            self._gen_function(args)

        else:
            self.parser.print_help()

    @staticmethod
    def render_jinja_mapping(jinja_mapping_dict, jinja_env, target_dir, package_dir):
        """
        Write all the Jinja Templates specified in jinja_mapping_dict that
        are found in the jinja_env to the target_dir. Returns a Tuple of
        newly generated files and files that were skipped

        :param jinja_mapping_dict: e.g. {"file_to_write.py": ("name_of_template.py.jinja2", jinja_data)}
        :param jinja_env: Jinja Environment
        :param target_dir: Path to write Templates to
        :return: newly_generated_files, files_skipped: a Tuple of newly generated files and files skipped
        :rtype: tuple
        """

        newly_generated_files = []
        files_skipped = []

        for (file_name, file_info) in jinja_mapping_dict.items():

            if isinstance(file_info, dict):
                # This is a sub directory
                sub_dir_mapping_dict = file_info
                path_sub_dir = os.path.join(target_dir, file_name)

                try:
                    os.makedirs(path_sub_dir)
                # Skip this error, which is generally a 'File Exists' error
                except OSError:
                    pass

                new_files, skipped_files = CmdCodegen.render_jinja_mapping(
                    jinja_mapping_dict=sub_dir_mapping_dict,
                    jinja_env=jinja_env,
                    target_dir=path_sub_dir,
                    package_dir=package_dir)

                newly_generated_files += new_files
                files_skipped += skipped_files

            elif isinstance(file_info, str) and os.path.isfile(file_info):
                # It is just a path to a file, copy it to the target_file
                target_file = os.path.join(target_dir, file_name)
                if os.path.exists(target_file):
                    # If file already exists skip copy.
                    files_skipped.append(os.path.relpath(target_file, start=package_dir))
                    continue

                newly_generated_files.append(os.path.relpath(target_file, start=package_dir))
                shutil.copy(file_info, target_file)

            else:
                # Get path to Jinja2 template
                path_template = file_info[0]

                # Get data dict for this Jinja2 template
                template_data = file_info[1]

                target_file = os.path.join(target_dir, file_name)

                if os.path.exists(target_file):
                    files_skipped.append(os.path.relpath(target_file, start=package_dir))
                    continue

                jinja_template = jinja_env.get_template(path_template)
                jinja_rendered_text = jinja_template.render(template_data)

                newly_generated_files.append(os.path.relpath(target_file, start=package_dir))

                sdk_helpers.write_file(target_file, jinja_rendered_text)

        return newly_generated_files, files_skipped

    @staticmethod
    def merge_codegen_params(old_params, args, mapping_tuples):
        """
        Merge any codegen params found in old_params and args.
        Return updated args

        :param old_params: List of Resilient Objects (normally result of calling customize_py.codegen_reload_data())
        :type old_params: List
        :param args: Namespace of all args passed from command line
        :type args: argparse.Namespace
        :param mapping_tuples: List of Tuples e.g. [("arg_name", "old_param_name")]
        :type mapping_tuples: List
        :return: The 'merged' args
        :rtype: argparse.Namespace
        """
        for m in mapping_tuples:
            all_obj_names_wanted = set()

            arg_name = m[0]
            old_param_name = m[1]

            arg = getattr(args, arg_name, None)
            if arg:
                all_obj_names_wanted = set(arg)

            setattr(args, arg_name, list(all_obj_names_wanted.union(set(old_params.get(old_param_name, [])))))

        return args

    @staticmethod
    def add_payload_samples(mapping_dict, fn_name, jinja_data):
        """
        Add a section to the mapping_dict for fn_name and
        for that function add a tuple with its jinja2 template
        location and the jinja_data to render it with.

        Note: as the mapping_dict is passed by reference,
        there is no need to return it

        :param mapping_dict: Dictionary of all the files to render
        :type mapping_dict: dict
        :param fn_name: Name of the Function
        :type fn_name: str
        :param jinja_data: A dictionary of the data to render the associated template with
        :type jinja_data: dict
        """
        # Create new dict for this fn
        ps_dict = mapping_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR][fn_name] = {}

        # Add to that dict
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EX_SUCCESS] = (u"{0}/mock_json_expectation_success.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EP_SUCCESS] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EX_FAIL] = (u"{0}/mock_json_expectation_fail.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EP_FAIL] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)

    @staticmethod
    def _gen_function(args):
        # TODO: Handle just generating a FunctionComponent for the /components directory
        LOG.info("codegen _gen_function called")

    @staticmethod
    def _gen_package(args, setup_py_attributes={}):

        LOG.info("Generating codegen package...")

        if os.path.exists(args.package) and not args.reload:
            raise SDKException(u"'{0}' already exists. Add --reload flag to regenerate it".format(args.package))

        if not sdk_helpers.is_valid_package_name(args.package):
            raise SDKException(u"'{0}' is not a valid package name".format(args.package))

        # The package_name will be specified in the args
        package_name = args.package

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

        # Get data required for Jinja2 templates from export
        jinja_data = sdk_helpers.get_from_export(org_export,
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
        jinja_data["export_data"] = sdk_helpers.minify_export(org_export,
                                                              message_destinations=sdk_helpers.get_object_api_names(ResilientObjMap.MESSAGE_DESTINATIONS, jinja_data.get("message_destinations")),
                                                              functions=sdk_helpers.get_object_api_names(ResilientObjMap.FUNCTIONS, jinja_data.get("functions")),
                                                              workflows=sdk_helpers.get_object_api_names(ResilientObjMap.WORKFLOWS, jinja_data.get("workflows")),
                                                              rules=sdk_helpers.get_object_api_names(ResilientObjMap.RULES, jinja_data.get("rules")),
                                                              fields=jinja_data.get("all_fields"),
                                                              artifact_types=sdk_helpers.get_object_api_names(ResilientObjMap.INCIDENT_ARTIFACT_TYPES, jinja_data.get("artifact_types")),
                                                              datatables=sdk_helpers.get_object_api_names(ResilientObjMap.DATATABLES, jinja_data.get("datatables")),
                                                              tasks=sdk_helpers.get_object_api_names(ResilientObjMap.TASKS, jinja_data.get("tasks")),
                                                              phases=sdk_helpers.get_object_api_names(ResilientObjMap.PHASES, jinja_data.get("phases")),
                                                              scripts=sdk_helpers.get_object_api_names(ResilientObjMap.SCRIPTS, jinja_data.get("scripts")))

        # Add package_name to jinja_data
        jinja_data["package_name"] = package_name

        # Add version
        jinja_data["version"] = setup_py_attributes.get("version", package_helpers.MIN_SETUP_PY_VERSION)

        # Validate we have write permissions
        sdk_helpers.validate_dir_paths(os.W_OK, output_base)

        if not args.reload:
            # If this is not a reload, join package_name to output base
            output_base = os.path.join(output_base, package_name)

        # If the output_base directory does not exist, create it
        if not os.path.exists(output_base):
            os.makedirs(output_base)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env("data/codegen/templates/package_template")

        # This dict maps our package file structure to  Jinja2 templates
        package_mapping_dict = {
            "MANIFEST.in": ("MANIFEST.in.jinja2", jinja_data),
            "README.md": ("README.md.jinja2", jinja_data),
            "setup.py": ("setup.py.jinja2", jinja_data),
            "tox.ini": ("tox.ini.jinja2", jinja_data),
            "Dockerfile": ("Dockerfile.jinja2", jinja_data),
            "entrypoint.sh": ("entrypoint.sh.jinja2", jinja_data),
            "apikey_permissions.txt": ("apikey_permissions.txt.jinja2", jinja_data),
            "data": {},
            "icons": {
                "company_logo.png": package_helpers.PATH_DEFAULT_ICON_COMPANY_LOGO,
                "app_logo.png": package_helpers.PATH_DEFAULT_ICON_EXTENSION_LOGO,
            },
            "doc": {
                "screenshots": {
                    "main.png": package_helpers.PATH_DEFAULT_SCREENSHOT
                }
            },
            package_name: {
                "__init__.py": ("package/__init__.py.jinja2", jinja_data),
                "LICENSE": ("package/LICENSE.jinja2", jinja_data),

                "components": {
                    "__init__.py": ("package/components/__init__.py.jinja2", jinja_data),
                },
                "util": {
                    "data": {
                        "export.res": ("package/util/data/export.res.jinja2", jinja_data)
                    },
                    "__init__.py": ("package/util/__init__.py.jinja2", jinja_data),
                    "config.py": ("package/util/config.py.jinja2", jinja_data),
                    "customize.py": ("package/util/customize.py.jinja2", jinja_data),
                    "selftest.py": ("package/util/selftest.py.jinja2", jinja_data),
                }
            }
        }

        # If there are Functions, add a 'tests' and a 'payload_samples' directory (if in dev mode)
        if jinja_data.get("functions"):
            package_mapping_dict["tests"] = {}

            if sdk_helpers.is_env_var_set(sdk_helpers.ENV_VAR_DEV):
                package_mapping_dict["payload_samples"] = {}

        # Loop each Function
        for f in jinja_data.get("functions"):
            # Add package_name to function data
            f["package_name"] = package_name

            # Get function name
            fn_name = f.get("export_key")

            # Generate function_component.py file name
            file_name = u"funct_{0}.py".format(fn_name)

            # Add to 'components' directory
            package_mapping_dict[package_name]["components"][file_name] = ("package/components/function.py.jinja2", f)

            # Add to 'tests' directory
            package_mapping_dict["tests"][u"test_{0}".format(file_name)] = ("tests/test_function.py.jinja2", f)

            # See if RES_SDK_DEV environment var is set
            if sdk_helpers.is_env_var_set(sdk_helpers.ENV_VAR_DEV):
                # Add a 'payload_samples/fn_name' directory and the files to it
                CmdCodegen.add_payload_samples(package_mapping_dict, fn_name, f)

        for w in jinja_data.get("workflows"):

            # Generate wf_xx.md file name
            file_name = u"wf_{0}.md".format(w.get(ResilientObjMap.WORKFLOWS))

            # Add workflow to data directory
            package_mapping_dict["data"][file_name] = ("data/workflow.md.jinja2", w)

        newly_generated_files, skipped_files = CmdCodegen.render_jinja_mapping(
            jinja_mapping_dict=package_mapping_dict,
            jinja_env=jinja_env,
            target_dir=output_base,
            package_dir=output_base)

        # Log new and skipped files
        if newly_generated_files:
            LOG.debug("Newly generated files:\n\t> %s", "\n\t> ".join(newly_generated_files))

        if skipped_files:
            LOG.debug("Files Skipped:\n\t> %s", "\n\t> ".join(skipped_files))

        LOG.info("'codegen' complete for '%s'", package_name)

        return output_base

    @staticmethod
    def _reload_package(args):

        old_params, path_customize_py_bak = [], ""

        # Get absolute path to package
        path_package = os.path.abspath(args.package)

        LOG.debug("\nPath to project: %s", path_package)

        # Ensure the package directory exists and we have WRITE access
        sdk_helpers.validate_dir_paths(os.W_OK, path_package)

        # Generate path to setup.py file + validate we have permissions to read it
        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)

        # Parse the setup.py file
        setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        package_name = setup_py_attributes.get("name")

        if not sdk_helpers.is_valid_package_name(package_name):
            raise SDKException(u"'{0}' is not a valid package name. 'name' attribute in setup.py file is not valid or not specified".format(package_name))

        LOG.debug("\nProject name: %s", package_name)

        # Generate path to customize.py file + validate we have permissions to read it
        path_customize_py = os.path.join(path_package, package_name, package_helpers.PATH_CUSTOMIZE_PY)
        sdk_helpers.validate_file_paths(os.W_OK, path_customize_py)

        # Set package + output args correctly (this handles if user runs 'codegen --reload -p .')
        args.package = package_name
        args.output = path_package

        LOG.info("'codegen --reload' started for '%s'", args.package)

        # Load the customize.py module
        customize_py_module = package_helpers.load_customize_py_module(path_customize_py, warn=False)

        try:
            # Get the 'old_params' from customize.py
            old_params = customize_py_module.codegen_reload_data()
        except AttributeError:
            raise SDKException(u"Corrupt customize.py. No reload method found in {0}".format(path_customize_py))

        if not old_params:
            raise SDKException(u"No reload params found in {0}".format(path_customize_py))

        # Rename the old customize.py with .bak
        path_customize_py_bak = sdk_helpers.rename_to_bak_file(path_customize_py)

        # If local export file exists then save it to a .bak file.
        # (Older packages may not have the /util/data/export.res file)
        path_export_res = os.path.join(path_package, package_name,
                                       package_helpers.PATH_UTIL_DATA_DIR,
                                       package_helpers.BASE_NAME_LOCAL_EXPORT_RES)
        if os.path.isfile(path_export_res):
            path_export_res_bak = sdk_helpers.rename_to_bak_file(path_export_res)
        else:
            path_export_res_bak = None

        try:
            # Map command line arg name to dict key returned by codegen_reload_data() in customize.py
            mapping_tuples = [
                ("messagedestination", "message_destinations"),
                ("function", "functions"),
                ("workflow", "workflows"),
                ("rule", "actions"),
                ("field", "incident_fields"),
                ("artifacttype", "incident_artifact_types"),
                ("datatable", "datatables"),
                ("task", "automatic_tasks"),
                ("script", "scripts")
            ]

            # Merge old_params with new params specified on command line
            args = CmdCodegen.merge_codegen_params(old_params, args, mapping_tuples)

            # Parse the setup.py file
            setup_py_attributes = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

            LOG.debug("Regenerating codegen '%s' package now", args.package)

            # Regenerate the package
            path_reloaded = CmdCodegen._gen_package(args, setup_py_attributes=setup_py_attributes)

            LOG.info("\nNOTE: Ensure the MANIFEST.in file includes line:\nrecursive-include %s/util *\n", args.package)
            LOG.info("'codegen --reload' complete for '%s'", args.package)

            return path_reloaded

        # This is required in finally block as user may kill using keyboard interrupt
        finally:
            # If an error occurred, customize.py does not exist, rename the backup file to original
            if not os.path.isfile(path_customize_py):
                LOG.info(u"An error occurred. Renaming customize.py.bak to customize.py")
                sdk_helpers.rename_file(path_customize_py_bak, package_helpers.BASE_NAME_CUSTOMIZE_PY)
            if not os.path.isfile(path_export_res) and path_export_res_bak:
                LOG.info(u"An error occurred. Renaming export.res.bak to export.res")
                sdk_helpers.rename_file(path_export_res_bak, package_helpers.BASE_NAME_LOCAL_EXPORT_RES)
