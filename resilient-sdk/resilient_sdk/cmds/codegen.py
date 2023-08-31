#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

""" Implementation of `resilient-sdk codegen` """

import json
import logging
import os
import re
import shutil
from datetime import datetime

from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import constants
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util.resilient_objects import ResilientObjMap, MD_FILE_PROPERTIES
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_genson_overwrites import main_genson_builder_overwrites, CustomSchemaBuilder

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)


class CmdCodegen(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "codegen"
    CMD_HELP = "Generates boilerplate code used to begin developing an app."
    CMD_USAGE = """
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two' -i 'custom incident type'
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' --rule 'Rule One' 'Rule Two' --settings <path_to_custom_sdk_settings_file>
    $ resilient-sdk codegen -p <name_of_package> -m 'fn_custom_md' -c '/usr/custom_app.config'
    $ resilient-sdk codegen -p <path_current_package> --reload --workflow 'new_wf_to_add'
    $ resilient-sdk codegen -p <path_current_package> --poller
    $ resilient-sdk codegen -p <path_current_package> --gather-results
    $ resilient-sdk codegen -p <path_current_package> --gather-results '/usr/custom_app.log' -f 'func_one' 'func_two'"""
    CMD_DESCRIPTION = CMD_HELP
    CMD_ADD_PARSERS = ["app_config_parser", "res_obj_parser", "io_parser", constants.SDK_SETTINGS_PARSER_NAME]

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

        self.parser.add_argument("-pr", "--poller",
                                 action="store_true",
                                 help="Build template files for a poller")

        self.parser.add_argument(constants.SUB_CMD_OPT_GATHER_RESULTS,
                                 action="store",
                                 nargs="?",
                                 const=constants.PATH_RES_DEFAULT_LOG_FILE,
                                 help="Uses the log file specified or if no path specified use the default at '~/.resilient/logs/app.log' to try gather results. Only Python >= 3.6 supported")

    def execute_command(self, args):
        LOG.debug("called: CmdCodegen.execute_command()")

        if args.gather_results:
            if not args.package:
                raise SDKException("'-p' must be specified when using '{0}'".format(constants.SUB_CMD_OPT_GATHER_RESULTS))

            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, constants.SUB_CMD_OPT_GATHER_RESULTS)
            self._get_results_from_log_file(args)

        elif args.reload:
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
                # Initialize variable for target file name from export.
                export_target_file = None
                # Get path to Jinja2 template
                path_template = file_info[0]

                # Get data dict for this Jinja2 template
                template_data = file_info[1]
                target_file = os.path.join(target_dir, file_name)
                # Get target file extension.
                target_ext = os.path.splitext(target_file)[1]
                # Try to set object name to function name if it exists in export.
                export_obj_name = template_data.get(ResilientObjMap.FUNCTIONS)
                if not export_obj_name:
                    # Not a function try to set to workflow name from export instead.
                    export_obj_name = template_data.get(ResilientObjMap.WORKFLOWS)

                if export_obj_name:
                    # Is a function or workflow so get file path(s) using export object name.
                    if os.path.dirname(path_template) == "tests":
                        export_target_file = os.path.join(target_dir, u"test_{0}{1}".format(export_obj_name, target_ext))
                    else:
                        export_target_file = os.path.join(target_dir, u"{0}{1}".format(export_obj_name, target_ext))

                write_target_file = None
                for t_file in [target_file, export_target_file]:
                    if t_file and os.path.exists(t_file):
                        # Don't skip for workflows.
                        if target_ext == ".md" and export_target_file:
                            # Write to first workflow target file name format found.
                            write_target_file = t_file
                        else:
                            files_skipped.append(os.path.relpath(t_file, start=package_dir))
                            write_target_file = None
                        break
                    if t_file and not write_target_file:
                        # We will use default (target_file) format if file doesn't already exist.
                        write_target_file = t_file

                if not write_target_file:
                    continue

                jinja_template = jinja_env.get_template(path_template)
                jinja_rendered_text = jinja_template.render(template_data)

                newly_generated_files.append(os.path.relpath(write_target_file, start=package_dir))

                sdk_helpers.write_file(write_target_file, jinja_rendered_text)

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

        # TODO: re-enable this code when we have logic to use mock_server files
        """
        if sdk_helpers.is_env_var_set(constants.ENV_VAR_DEV):
            ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EX_SUCCESS] = (u"{0}/mock_json_expectation_success.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
            ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EP_SUCCESS] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
            ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EX_FAIL] = (u"{0}/mock_json_expectation_fail.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
            ps_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EP_FAIL] = (u"{0}/blank.json.jinja2".format(package_helpers.PATH_TEMPLATE_PAYLOAD_SAMPLES), jinja_data)
        """

    @staticmethod
    def _check_and_create_md_files(package_mapping_dict, object_type, jinja_data):
        """
        Creates md files for workflows and playbooks using jinja2 templates.
        
        Note: as the mapping_dict is passed by reference,
        there is no need to return it.
        
        :param package_mapping_dict: Dictionary of all the files to render
        :type package_mapping_dict: dict
        :param object_type: Type of object to create md files for (workflow or playbook)
        :type object_type: str
        :param jinja_data: A dictionary of the data to render the associated template with
        :type jinja_data: dict
        """
        _obj_properties = MD_FILE_PROPERTIES[object_type]

        # Get a list of workflow/playbooks names in export.
        ob_names = [obj.get(_obj_properties["ResilientObj"]) for obj in jinja_data.get(object_type)]

        for obj in jinja_data.get(object_type, []):
            # Get workflow/playbooks name
            ob_name = obj.get(_obj_properties["ResilientObj"])

            # add sdk version to workflow data
            obj["sdk_version"] = sdk_helpers.get_resilient_sdk_version()

            # Generate pb_xx.md/wf_xx.md file name
            # Don't add prefix if workflow/playbook name already begins with "wf_/pb_".
            if re.search(_obj_properties["prefix_pattern"], ob_name):
                file_name = u"{0}.md".format(ob_name)
            else:
                file_name = _obj_properties["obj_file_name"].format(ob_name)
                # Check if file_name without extension already exists in workflow/playbooks names list.
                if os.path.splitext(file_name)[0] in ob_names:
                    raise SDKException(u"File name '{0}' already in use please recreate the {1} '{2}'."
                        .format(file_name, object_type, ob_name))

            # Add workflow/playbook to data directory
            package_mapping_dict["data"][file_name] = (_obj_properties["jinja_file_path"], obj)

    @staticmethod
    def _gen_function(args):
        # TODO: Handle just generating a FunctionComponent for the /components directory
        LOG.info("codegen _gen_function called")

    @staticmethod
    def _gen_package(args, setup_py_attributes={}):

        LOG.info("Generating codegen package...")

        sdk_helpers.is_python_min_supported_version()

        if os.path.exists(args.package) and not args.reload:
            raise SDKException(u"'{0}' already exists. Add --reload flag to regenerate it".format(args.package))

        if not sdk_helpers.is_valid_package_name(args.package):
            raise SDKException(u"'{0}' is not a valid package name".format(args.package))

        # The package_name will be specified in the args
        package_name = args.package

        # Validate that the given path to the sdk settings is valid
        try:
            sdk_helpers.validate_file_paths(os.R_OK, args.settings)
            # Parse the sdk_settings.json file
            settings_file_contents = sdk_helpers.read_json_file(args.settings, "codegen")
        except SDKException as err:
            args.settings = None
            settings_file_contents = {}
            LOG.debug("Given path to SDK Settings is either not valid or not readable. Ignoring and using built-in values for codegen")

        # Get output_base, use args.output if defined, else current directory
        output_base = args.output if args.output else os.curdir
        output_base = os.path.abspath(output_base)

        # If --exportfile is specified, read org_export from that file
        if args.exportfile:
            LOG.info("Using local export file: %s", args.exportfile)
            org_export = sdk_helpers.read_local_exportfile(args.exportfile)

        else:
            # Instantiate connection to SOAR
            res_client = sdk_helpers.get_resilient_client(path_config_file=args.config)

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
                                                 scripts=args.script,
                                                 incident_types=args.incidenttype,
                                                 playbooks=args.playbook)

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
                                                              scripts=sdk_helpers.get_object_api_names(ResilientObjMap.SCRIPTS, jinja_data.get("scripts")),
                                                              incident_types=sdk_helpers.get_object_api_names(ResilientObjMap.INCIDENT_TYPES, jinja_data.get("incident_types")),
                                                              playbooks=sdk_helpers.get_object_api_names(ResilientObjMap.PLAYBOOKS, jinja_data.get("playbooks")))

        # Add package_name to jinja_data
        jinja_data["package_name"] = package_name

        # Add version
        jinja_data["version"] = setup_py_attributes.get("version", package_helpers.MIN_SETUP_PY_VERSION)

        jinja_data["resilient_libraries_version"] = sdk_helpers.get_resilient_libraries_version_to_use()

        # add poller flag
        jinja_data["poller_flag"] = args.poller

        # add ::CHANGE_ME:: to jinja data
        jinja_data["change_me_str"] = constants.DOCGEN_PLACEHOLDER_STRING

        # add license name, author, author_email, url
        settings_file_contents_setup = settings_file_contents.get("setup", {})
        jinja_data["license"] = settings_file_contents_setup.get("license", constants.CODEGEN_DEFAULT_SETUP_PY_LICENSE)
        jinja_data["author"] = settings_file_contents_setup.get("author", constants.CODEGEN_DEFAULT_SETUP_PY_AUTHOR)
        jinja_data["author_email"] = settings_file_contents_setup.get("author_email", constants.CODEGEN_DEFAULT_SETUP_PY_EMAIL)
        jinja_data["url"] = settings_file_contents_setup.get("url", constants.CODEGEN_DEFAULT_SETUP_PY_URL)
        jinja_data["long_description"] = settings_file_contents_setup.get("long_description", constants.CODEGEN_DEFAULT_SETUP_PY_LONG_DESC)

        # add license_content to jinja_data and format in year if applicable
        year = datetime.now().year
        jinja_data["license_content"] = settings_file_contents.get("license_content", constants.CODEGEN_DEFAULT_LICENSE_CONTENT).format(year)
        # add current SDK version to jinja data
        jinja_data["sdk_version"] = sdk_helpers.get_resilient_sdk_version()
        # add copyright info with year to jinja_data if present in settings_file
        # and left-strip any leading "#" so that it fits well in the jinja template
        copyright_str = str(settings_file_contents.get("copyright", constants.CODEGEN_DEFAULT_COPYRIGHT_CONTENT)).lstrip("#").format(year)
        jinja_data["copyright"] = copyright_str

        # Validate we have write permissions
        sdk_helpers.validate_dir_paths(os.W_OK, output_base)

        if not args.reload:
            # If this is not a reload, join package_name to output base
            output_base = os.path.join(output_base, package_name)

        # If the output_base directory does not exist, create it
        if not os.path.exists(output_base):
            os.makedirs(output_base)

        # Instansiate Jinja2 Environment with path to Jinja2 templates
        jinja_env = sdk_helpers.setup_jinja_env(constants.PACKAGE_TEMPLATE_PATH)

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

        # poller logic if --poller flag was passed
        if args.poller:
            poller_mapping_dict = {
                "__init__.py": ("package/poller/__init__.py.jinja2", jinja_data),
                "poller.py": ("package/poller/poller.py.jinja2", jinja_data),
                # data isn't rendered with jinja — these are default jinja templates to be modified
                # by the developer who is implementing a poller
                "data": {
                    package_helpers.BASE_NAME_POLLER_CREATE_CASE_TEMPLATE: package_helpers.PATH_DEFAULT_POLLER_CREATE_TEMPLATE,
                    package_helpers.BASE_NAME_POLLER_UPDATE_CASE_TEMPLATE: package_helpers.PATH_DEFAULT_POLLER_UPDATE_TEMPLATE,
                    package_helpers.BASE_NAME_POLLER_CLOSE_CASE_TEMPLATE: package_helpers.PATH_DEFAULT_POLLER_CLOSE_TEMPLATE
                }
            }
            lib_mapping_dict = {
                "__init__.py": ("package/lib/__init__.py.jinja2", jinja_data),
                "app_common.py": ("package/lib/app_common.py.jinja2", jinja_data)
            }
            package_mapping_dict[package_name]['poller'] = poller_mapping_dict
            package_mapping_dict[package_name]['lib'] = lib_mapping_dict

        # If there are Functions, add a 'tests' and a 'payload_samples' directory (if in dev mode)
        if jinja_data.get("functions"):
            package_mapping_dict["tests"] = {}
            package_mapping_dict[package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR] = {}

        # Get a list of function names in export.
        fn_names = [f.get(ResilientObjMap.FUNCTIONS) for f in jinja_data.get("functions")]

        # Loop each Function
        for f in jinja_data.get("functions"):
            # Add package_name to function data
            f["package_name"] = package_name

            # add sdk version to function data
            f["sdk_version"] = sdk_helpers.get_resilient_sdk_version()
            f["copyright"] = copyright_str

            # Get function name
            fn_name = f.get(ResilientObjMap.FUNCTIONS)

            # Generate funct_function_component.py file name
            # Don't add prefix if function name already begins with "func_" or "funct_".
            if re.search(r"^(func|funct)_", fn_name):
                file_name = u"{0}.py".format(fn_name)
            else:
                file_name = u"funct_{0}.py".format(fn_name)
                # Check if file_name without extension already exists in functions names list.
                if os.path.splitext(file_name)[0] in fn_names:
                    raise SDKException(u"File name '{0}' already in use please rename the function '{1}'."
                                       .format(file_name, fn_name))

            # Add an 'atomic function' to 'components' directory else add a 'normal function'
            package_mapping_dict[package_name]["components"][file_name] = ("package/components/atomic_function.py.jinja2", f)

            # Add to 'tests' directory
            package_mapping_dict["tests"][u"test_{0}".format(file_name)] = ("tests/test_function.py.jinja2", f)

            # Add a 'payload_samples/fn_name' directory and the files to it
            CmdCodegen.add_payload_samples(package_mapping_dict, fn_name, f)

        # checks and creates data for .md files for workflow
        CmdCodegen._check_and_create_md_files(package_mapping_dict, "workflows", jinja_data)

        # checks and creates .md files for playbooks
        CmdCodegen._check_and_create_md_files(package_mapping_dict, "playbooks", jinja_data)

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

        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)

        package_name = package_helpers.get_package_name(path_package)

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
                ("incidenttype", "incident_types"),
                ("datatable", "datatables"),
                ("task", "automatic_tasks"),
                ("script", "scripts"),
                ("playbook", "playbooks")
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

    @classmethod
    def _get_results_from_log_file(cls, args):
        """
        - Gets all function names from the payload_samples directory
        - Traverses the file at the path specified by args.gather_results (in a reversed order)
        - Looks for lines containing ``[<fn_name>] Result: {'version': 2.0, 'success': True...``
        - Parses it and generates an output_json_example.json and output_json_schema.json file for each ``Result`` found
        - Uses the libary ``genson`` to generate the JSON schema from a Python Dictionary

        :param args: (required) the cmd line arguments
        :type args: argparse.ArgumentParser
        :raises: an SDKException if args.package is not a valid path
        """

        # Check if Python >= MIN_SUPPORTED_PY_VERSION
        if not sdk_helpers.is_python_min_supported_version(constants.ERROR_WRONG_PYTHON_VERSION):
            raise SDKException(constants.ERROR_WRONG_PYTHON_VERSION)

        path_package = os.path.abspath(args.package)
        path_log_file = args.gather_results
        path_payload_samples_dir = os.path.join(path_package, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR)

        LOG.debug("\nPath to project: %s", path_package)

        sdk_helpers.validate_dir_paths(os.W_OK, path_package)

        package_name = package_helpers.get_package_name(path_package)

        LOG.info("'codegen %s' started for '%s'", constants.SUB_CMD_OPT_GATHER_RESULTS, package_name)
        try:

            sdk_helpers.validate_dir_paths(os.W_OK, path_payload_samples_dir)

        except SDKException as e:

            if constants.ERROR_NOT_FIND_DIR in e.message:
                LOG.warning("WARNING: no '%s' found. Running 'codegen --reload' to create the default missing files\n%s", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_DIR, constants.LOG_DIVIDER)
                args.reload = True
                cls._reload_package(args)
                LOG.warning(constants.LOG_DIVIDER)

            else:
                raise e

        functions_that_need_payload_samples = args.function if args.function else os.listdir(path_payload_samples_dir)

        results_scraped = sdk_helpers.scrape_results_from_log_file(path_log_file)

        for fn_name in functions_that_need_payload_samples:

            fn_results = results_scraped.get(fn_name)

            if not fn_results:
                package_helpers.color_output("WARNING: No results could be found for '{0}' in '{1}'".format(fn_name, path_log_file), constants.VALIDATE_LOG_LEVEL_WARNING, do_print=True)
                continue

            LOG.info("Results found for '[%s]'", fn_name)

            path_payload_samples_fn_name = os.path.join(path_payload_samples_dir, fn_name)
            path_output_json_example = os.path.join(path_payload_samples_fn_name, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)
            path_output_json_schema = os.path.join(path_payload_samples_fn_name, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)

            path_output_json_example_bak = sdk_helpers.rename_to_bak_file(path_output_json_example)
            path_output_json_schema_bak = sdk_helpers.rename_to_bak_file(path_output_json_schema)

            try:
                LOG.debug("Writing JSON example file for '%s' to '%s'", fn_name, path_output_json_example)
                sdk_helpers.write_file(path_output_json_example, json.dumps(fn_results, indent=2))

                LOG.debug("Writing JSON schema file for '%s' to '%s'", fn_name, path_output_json_schema)
                builder = CustomSchemaBuilder(schema_uri=constants.CODEGEN_JSON_SCHEMA_URI)
                main_genson_builder_overwrites(builder)
                builder.add_object(fn_results)
                sdk_helpers.write_file(path_output_json_schema, builder.to_json(indent=2))

            finally:
                if not os.path.isfile(path_output_json_example) and path_output_json_example_bak:
                    LOG.info(u"An error occurred. Renaming %s.bak to %s", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)
                    sdk_helpers.rename_file(path_output_json_example_bak, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_EXAMPLE)

                if not os.path.isfile(path_output_json_schema) and path_output_json_schema_bak:
                    LOG.info(u"An error occurred. Renaming %s.bak to %s", package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)
                    sdk_helpers.rename_file(path_output_json_schema_bak, package_helpers.BASE_NAME_PAYLOAD_SAMPLES_SCHEMA)

        LOG.info("'codegen %s' complete for '%s'", constants.SUB_CMD_OPT_GATHER_RESULTS, package_name)
