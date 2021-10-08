#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" Implementation of `resilient-sdk validate` """

import logging
import os, re
from xml.etree.ElementTree import parse
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue
from resilient_sdk.util.resilient_objects import ResilientObjMap
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import sdk_validate_configs as val_configs

# Get the same logger object that is used in app.py
LOG = logging.getLogger(sdk_helpers.LOGGER_NAME)

SUB_CMD_VALIDATE = ("--validate", )
SUB_CMD_TESTS = ("--tests", )
SUB_CMD_PYLINT = ("--pylint", )
SUB_CMD_BANDIT = ("--bandit", )
SUB_CMD_CVE = ("--cve", )


class CmdValidate(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "validate"
    CMD_HELP = "Validate an App before packaging it"
    CMD_USAGE = """
    $ resilient-sdk validate -p <name_of_package>
    $ resilient-sdk validate -p <name_of_package> --validate
    $ resilient-sdk validate -p <name_of_package> --tests
    $ resilient-sdk validate -p <name_of_package> --pylint --bandit --cve"""
    CMD_DESCRIPTION = CMD_HELP

    VALIDATE_ISSUES = []

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION

        # Add any positional or optional arguments here
        self.parser.add_argument(sdk_helpers.SUB_CMD_PACKAGE[1], sdk_helpers.SUB_CMD_PACKAGE[0],
                                 type=ensure_unicode,
                                 required=True,
                                 help="(required) Path to existing package")

        self.parser.add_argument(SUB_CMD_VALIDATE[0],
                                 action="store_true",
                                 help="Run validation of package files")

        self.parser.add_argument(SUB_CMD_TESTS[0],
                                 action="store_true",
                                 help="Run tests using package's tox.ini file in a Python 3.6 environment")

        self.parser.add_argument(SUB_CMD_PYLINT[0],
                                 action="store_true",
                                 help="Run a pylint scan of all .py files under package directory (if 'pylint' is installed")

        self.parser.add_argument(SUB_CMD_BANDIT[0],
                                 action="store_true",
                                 help="Run a bandit scan of all .py files under package directory (if 'bandit' is installed")

        self.parser.add_argument(SUB_CMD_CVE[0],
                                 action="store_true",
                                 help="Run a safety scan of all .py files under package directory (if 'safety' is installed")

    def execute_command(self, args):
        """
        TODO
        """
        LOG.info("{0}Running validate on '{1}'{0}".format(sdk_helpers.LOG_DIVIDER, args.package))

        self.VALIDATE_ISSUES += self._print_package_details(args)

        sdk_helpers.is_python_min_supported_version()

        if not args.validate and not args.tests and not args.pylint and not args.bandit and not args.cve:
            SDKException.command_ran = "{0} {1} | {2}".format(self.CMD_NAME, sdk_helpers.SUB_CMD_PACKAGE[0], sdk_helpers.SUB_CMD_PACKAGE[1])
            self._run_main_validation(args)
            exit(0)

        if args.validate:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_VALIDATE[0])
            self._validate(args)

        if args.tests:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_TESTS[0])
            self._run_tests(args)

        if args.pylint:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_PYLINT[0])
            self._run_pylint_scan(args)

        if args.bandit:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_BANDIT[0])
            self._run_bandit_scan(args)

        if args.cve:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_CVE[0])
            self._run_cve_scan(args)

    @classmethod
    def _run_main_validation(cls, args):
        """
        TODO
        """
        LOG.info("{0}Running main validation{0}".format(sdk_helpers.LOG_DIVIDER))
        cls.VALIDATE_ISSUES += cls._validate(args)
        cls.VALIDATE_ISSUES += cls._run_tests(args)

    @staticmethod
    def _print_package_details(args):
        """
        Print to the console the package details of the specified package
        including:
        - the absolute path of the package
        - display name of the package
        - name of the package
        - version of the package
        - version of SOAR the app was developed against
        - the python dependencies the app has
        - the name and email address of the developer
        - whether or not a proxy is supported

        Requires that args.package path contains:
        - setup.py
        - util/data/export.res
        - TODO: a file that specifies the location of proxy support??
                if running res-circuits >= sdk_helpers.RESILIENT_LIBRARIES_VERSION

        :param args: command line args
        :return: Prints output to the console and returns a list of SDKValidateIssues objects if it encountered
                 issues in parsing the package details
        :rtype: list of SDKValidateIssues that describes the issues found when running this method
        """
        LOG.info("{0}Printing details{0}".format(sdk_helpers.LOG_DIVIDER))

        # empty list of SDKValidateIssues
        issues = []
        # list of string for output
        package_details_output = [""]

        # Get absolute path to package
        path_package = os.path.abspath(args.package)

        LOG.debug("Path to project: {0}".format(path_package))

        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)
        # Generate path to setup.py file + validate we have permissions to read it
        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)

        parsed_setup_file = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        # check through setup.py file parse
        for attr in package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES:
            if attr != "description" and attr != "long_description" and attr != "entry_points": 
                attr_val = parsed_setup_file.get(attr)
                package_details_output.append("{0}: {1}".format(attr, attr_val if attr_val else "**NOT FOUND**"))

        # parse import definition from export.res file or from customize.py (deprecated)
        try:
            path_export_res = os.path.join(path_package, parsed_setup_file.get("name"), 
                                    package_helpers.PATH_UTIL_DATA_DIR, package_helpers.BASE_NAME_EXPORT_RES)
            sdk_helpers.validate_file_paths(os.R_OK, path_export_res)
            import_definition = package_helpers.get_import_definition_from_local_export_res(path_export_res)
        except SDKException as e:
            LOG.warning("WARNING: your code was generated with an older version of resilient-sdk. Please use the latest version and reload")

            path_customize_py = os.path.join(path_package, parsed_setup_file.get("name"), package_helpers.PATH_CUSTOMIZE_PY)
            sdk_helpers.validate_file_paths(os.R_OK, path_customize_py)
            import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py)
        except Exception as e:
            package_details_output.append("SOAR version: NOT FOUND; <path_to_package>/<package_name>/util/data/export.res not found")
        
        if import_definition and import_definition.get("server_version").get("version"):
            package_details_output.append("SOAR version: {0}".format(import_definition.get("server_version").get("version")))
        else:
            package_details_output.append("SOAR version: not specified in 'util/data/export.res'")

        if "": #TODO: PROXY NOT SUPPORT CHECK"
            package_details_output.append("Proxy supported: {0}".format())

        LOG.info("\n\t".join(package_details_output))

        return issues

    @staticmethod
    def _validate(args):
        """
        Wrapper method that validates the contents of the following files in the package dir:
        - setup.py 
        - fn_package/util/config.py
        - fn_package/util/customize.py
        - fn_package/util/selftest.py
        - fn_package/LICENSE
        - fn_package/icons
        - README.md
        - MANIFEST.in
        - apikey_permissions (optional but warn that should be App Host supported and give help/link to show how to convert to AppHost)
        - entrypoint.sh (optional but warn that should be App Host supported)
        - Dockerfile (optional but warn that should be App Host supported)

        :param args: list of args
        :return: list of issues of type SDKValidateIssue 
        :rtype: list of SDKValidateIssue
        """
        
        issues = []
        setup_pass = True

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        try:
            sdk_helpers.validate_dir_paths(os.R_OK, path_package)
        except Exception as e:
            raise e

        ##############
        ## SETUP.PY ##
        ##############
        # Generate path to setup.py file + validate we have permissions to read it
        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)
        try:
            sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)
            LOG.info("setup.py file found at path {0}\n".format(path_setup_py_file))
        except SDKException as e:
            raise e

        results = CmdValidate._validate_setup(path_package, path_setup_py_file)
        issues += results[0]
        setup_pass = results[1]

        CmdValidate._print_summary(issues)
        exit(0)
        return issues
        # TODO: implement other static validates
        #       - fn_package/util/config.py
        #       - fn_package/util/customize.py
        #       - fn_package/util/selftest.py
        #       - fn_package/LICENSE
        #       - fn_package/icons
        #       - README.md
        #       - MANIFEST.in
        #       - apikey_permissions (optional but warn that should be App Host supported and give help/link to show how to convert to AppHost)
        #       - entrypoint.sh (optional but warn that should be App Host supported)
        #       - Dockerfile (optional but warn that should be App Host supported)

    @staticmethod
    def _validate_setup(path_package, path_setup_py_file):
        """
        Validate the contents of the setup.py file in the given package:
        - CRITICAL: Check the file exists
        - CRITICAL: name: is all lowercase and only special char allowed is underscore
        - WARN: display_name: check does not start with <<
        - CRITICAL: license: check does not start with << or is none of any of the GPLs
        - CRITICAL: author: does not start with <<
        - CRITICAL: author_email: does not include "@example.com"
        - CRITICAL: description: does start with default "Resilient Circuits Components" - give detail where in the UI this will be displayed
        - CRITICAL: long_description: does start with default "Resilient Circuits Components" - give detail where in the UI this will be displayed
        - CRITICAL: install_requires: includes resilient_circuits or resilient-circuits at a minimum
        - WARN: checks if exists and WARNS the user if not "python_requires='>=3.6'"
        - CRITICAL: entry_points: that .configsection, .customize, .selftest
        - WARN: entry_points: if not a least one .component exists

        Requires that args.package path contains:
        - setup.py

        :param args: command line args
        :return: Returns a list of SDKValidateIssues that describes the issues found when running this method
        :rtype: list of SDKValidateIssues
        """
        LOG.info("{0}Validating setup.py{0}".format(sdk_helpers.LOG_DIVIDER))
        
        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if setup passes validation
        setup_valid = True

        LOG.debug("Path to project: {0}".format(path_package))

        attributes = val_configs.setup_py_attributes

        # check through setup.py file parse
        for attr in attributes:
            attr_dict = attributes.get(attr)
            parsed_attr = package_helpers.parse_setup_py(path_setup_py_file, [attr]).get(attr)

            fail_func = attr_dict.get("fail_func")
            severity = attr_dict.get("severity")
            fail_msg = attr_dict.get("fail_msg")
            missing_msg = attr_dict.get("missing_msg")
            solution = attr_dict.get("solution")

            if not parsed_attr:
                name = "{0} not found".format(attr)
                description = missing_msg.format(attr)
            elif fail_func(parsed_attr):
                formats = [attr, parsed_attr]
                if attr_dict.get("fail_msg_lambda_supplement"):
                    formats.append(attr_dict.get("fail_msg_lambda_supplement")(parsed_attr))

                name = "invalid values in setup.py"
                description = fail_msg.format(*formats)
            else:
                # TODO: @shane thoughts on creating a SDKValidateIssue object that will LOG.debug on success?
                # this helps us keep track for summary at the end but won't output unless the user sets log level=debug
                name = "{0} valid in setup.py".format(attr)
                description = "'{0}' passed".format(attr)
                severity = SDKValidateIssue.SEVERITY_LEVEL_DEBUG
                solution = ""
            issue = SDKValidateIssue(
                name,
                description,
                severity=severity,
                solution=solution.format(attr)
            )

            issues.append(issue)
            if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL: setup_valid = False

        # TODO: ENTRY_POINTS parse
        # SUPPORTED_EP

        issues.sort()
        for issue in issues:
            LOG.log(issue.get_logging_level(), issue.error_str())

        status_str = "PASS" if setup_valid else "FAIL"
        LOG.info(package_helpers.color_output("{0}setup.py validation {1}{0}".format(
            sdk_helpers.LOG_DIVIDER, 
            status_str
        ), status_str))
        return issues, setup_valid

    @staticmethod
    def _run_tests(args):
        """
        TODO
        """
        LOG.info("{0}Running tests{0}".format(sdk_helpers.LOG_DIVIDER))

    @staticmethod
    def _run_pylint_scan(args):
        """
        TODO
        """
        LOG.info("{0}Running pylint{0}".format(sdk_helpers.LOG_DIVIDER))

    @staticmethod
    def _run_bandit_scan(args):
        """
        TODO
        """
        LOG.info("{0}Running bandit{0}".format(sdk_helpers.LOG_DIVIDER))

    @staticmethod
    def _run_cve_scan(args):
        """
        TODO
        """
        LOG.info("{0}Running safety{0}".format(sdk_helpers.LOG_DIVIDER))

    @staticmethod
    def _print_summary(issues_list):
        counts = {
            SDKValidateIssue.SEVERITY_LEVEL_CRITICAL: 0,
            SDKValidateIssue.SEVERITY_LEVEL_WARN: 0,
            SDKValidateIssue.SEVERITY_LEVEL_INFO: 0,
            SDKValidateIssue.SEVERITY_LEVEL_DEBUG: 0,
        }
        for issue in issues_list:
            counts[issue.severity] += 1
        
        LOG.info("{0}Results{0}".format(sdk_helpers.LOG_DIVIDER))
        LOG.info(sdk_helpers.LOG_DIVIDER)
        LOG.info("Critical Issues: {0:>14}".format(
            package_helpers.color_output(counts[SDKValidateIssue.SEVERITY_LEVEL_CRITICAL], "CRITICAL")
        ))
        LOG.info("Warnings: {0:>21}".format(package_helpers.color_output(counts[SDKValidateIssue.SEVERITY_LEVEL_WARN], "WARNING")))
        LOG.info("Components Passed: {0:>12}".format(package_helpers.color_output(
            int(counts[SDKValidateIssue.SEVERITY_LEVEL_DEBUG] + counts[SDKValidateIssue.SEVERITY_LEVEL_INFO]), "PASS")
        ))
        LOG.info("\nSee the detailed report at TODO: <path_to_report>") # TODO
        LOG.info(sdk_helpers.LOG_DIVIDER)

        