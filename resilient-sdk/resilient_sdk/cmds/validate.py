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

        absolute_path = "Absolute path to package: {0}".format(path_package)

        attributes_to_parse = [
            "display_name",
            "name",
            "version",
            "author",
            "author_email",
            "install_requires",
            "python_requires"
        ]
        parsed_setup_file = package_helpers.parse_setup_py(path_setup_py_file, attributes_to_parse)

        # check through setup.py file parse
        for attr in attributes_to_parse:
            package_details_output.append("{0}: {1}".format(attr, parsed_setup_file.get(attr)))

        # parse import definition from export.res file
        path_export_res = os.path.join(path_package, parsed_setup_file.get("name"), 
                                       package_helpers.PATH_UTIL_DATA_DIR, package_helpers.BASE_NAME_EXPORT_RES)
        sdk_helpers.validate_file_paths(os.R_OK, path_export_res)
        import_definition = package_helpers.get_import_definition_from_local_export_res(path_export_res)

        if import_definition.get("server_version").get("version"):
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

        :param: 
        :return: 
        :rtype: 
        """
        LOG.info("{0}Validating{0}".format(sdk_helpers.LOG_DIVIDER))
        
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
        except Exception as e:
            raise e

        res = CmdValidate._validate_setup(path_package, path_setup_py_file)
        issues += res[0]
        setup_pass = res[1]

        print("\n***ISSUES***\n\t", "\n\t".join((str(i) for i in issues)))
        print("\n***SETUP PASSS?***",setup_pass)

        exit(0)
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
        
        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if setup passes validation
        setup_valid = True

        LOG.debug("Path to project: {0}".format(path_package))

        # each attribute has format (<name>, <regex to match to fail>, <failure message>, <severity>)
        attributes = {
            "name": {
                "pattern": "r[^a-z_]+", # TODO: are numbers allowed?
                "fail_msg": "setup.py attribute '{0}' is has the following invalid character(s): '{1}'",
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "make sure that '{0}' is all lowercase and does not include and special characters besides underscores",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            },
            "display_name": {
                "pattern": r"^<<|>>$", 
                "fail_msg": "setup.py attribute '{0}' appears to still be the default value", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "please set '{0}' to an appropriate value. this value will be displayed when the integration is installed",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_MED
            },
            "license": {
                "pattern": r"^<<|>>$", # TODO: what are the GPL's?
                "fail_msg": "setup.py attribute '{0}' appears to still be the default value", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "please set '{0}' to an appropriate value. more info HERE", # TODO: documentation link 
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            },
            "author": {
                "pattern": r"^<<|>>$", 
                "fail_msg": "setup.py attribute '{0}' appears to still be the default value", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "please set '{0}' to the name of the author",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            },
            "author_email": {
                "pattern": r"@example\.com", 
                "fail_msg": "setup.py attribute '{0}' appears to still be the default value. validation found invalid address '{1}'", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "please set '{0}' to the author's contact email",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            },
            "description": {
                "pattern": r"^(?!Resilient Circuits Components).+", 
                "fail_msg": "setup.py attribute '{0}' doesn't start with 'Resilient Circuits Components'", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "'{0}' should start with 'Resilient Circuits Components'. This will be displayed when the integration is installed",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_MED
            },
            "long_description": {
                "pattern": r"^(?!Resilient Circuits Components).+", 
                "fail_msg": "setup.py attribute '{0}' doesn't start with 'Resilient Circuits Components'", 
                "missing_msg": "setup.py file is missing attribute/or missing value for attribute '{0}'",
                "solution": "'{0}' should start with 'Resilient Circuits Components'. This will be displayed when the integration is installed",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_MED
            },
            # ATTRIBUTES BELOW HERE ARE MANUALLY PARSED - EXCLUDE "pattern" TO SKIP AUTOMATIC PARSING
            "install_requires": {
                "fail_msg": "'resilient_circuits' must be included as a dependency in 'install_requires'",
                "solution": "include 'resilient_circuits' as a requirement in 'install_requires'",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            },
            "python_requires": {
                "fail_msg": "given version '{0}.{1}' in setup.py is too low.",
                "missing_msg": "'python_requires' is a recommended attribute",
                "solution": "suggested requirement is 'python_requires>={0}.{1}".format(
                    sdk_helpers.MIN_SUPPORTED_PY_VERSION[0],
                    sdk_helpers.MIN_SUPPORTED_PY_VERSION[1]
                ),
                "sev": SDKValidateIssue.SEVERITY_LEVEL_MED
            },
            "entry_points": {
                "fail_msg": "", 
                "missing_msg": "",
                "solution": "",
                "sev": SDKValidateIssue.SEVERITY_LEVEL_HIGH
            }
        }

        # check through setup.py file parse
        for attr, attr_dict in attributes.items(): # TODO: @shane: ok to use py3 specific .items()?
            parsed_attr = package_helpers.parse_setup_py(path_setup_py_file, [attr]).get(attr)

            pattern = attr_dict.get("pattern")
            severity = attr_dict.get("sev")
            fail_msg = attr_dict.get("fail_msg")
            missing_msg = attr_dict.get("missing_msg")
            solution = attr_dict.get("solution")

            if not pattern:
                # cannot be parsed in loop; is dealt with below loop and can be skipped here
                continue

            if not parsed_attr:
                description = missing_msg.format(attr)

                issue = SDKValidateIssue(
                    "{0} not found".format(attr),
                    description,
                    severity=severity,
                    solution="please implement a value for attribute '{0}'".format(attr)
                )
                LOG.log(issue.get_logging_level(), issue.error_str())

                issues.append(issue)
                if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH: setup_valid = False
            else:
                matches = re.findall(pattern, str(parsed_attr))
                if matches:
                    fail_msg = fail_msg.format(*[attr, matches])
                    solution = solution.format(attr)

                    issue = SDKValidateIssue(
                        "invalid character(s) in setup.py",
                        fail_msg,
                        severity=severity,
                        solution=solution
                    )
                    LOG.log(issue.get_logging_level(), issue.error_str())

                    issues.append(issue)
                    if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH: setup_valid = False
                else:
                    pass # TODO: log info on success?

        # INSTALL_REQUIRES parse
        parsed_attr = package_helpers.parse_setup_py(path_setup_py_file, ["install_requires"]).get("install_requires")
        if not parsed_attr or not package_helpers.get_dependency_from_install_requires(parsed_attr, "resilient-circuits") \
            and not package_helpers.get_dependency_from_install_requires(parsed_attr, "resilient_circuits"):
            issue = SDKValidateIssue(
                "dependency issue for 'install_requires' in setup.py",
                attributes.get("install_requires").get("fail_msg"),
                severity=attributes.get("install_requires").get("sev"),
                solution=attributes.get("install_requires").get("solution")
            )
            LOG.log(issue.get_logging_level(), issue.error_str())

            issues.append(issue)
            if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH: setup_valid = False
        else:
            pass # TODO: deal with success

        # PYTHON_REQUIRES parse
        parsed_attr = package_helpers.parse_setup_py(path_setup_py_file, ["python_requires"]).get("python_requires")
        if parsed_attr and package_helpers.get_required_python_version(parsed_attr) < sdk_helpers.MIN_SUPPORTED_PY_VERSION:
            version = package_helpers.get_required_python_version(parsed_attr)
            issue = SDKValidateIssue(
                "python_requires version too low",
                attributes.get("python_requires").get("fail_msg").format(version[0], version[1]),
                severity=attributes.get("python_requires").get("sev"),
                solution=attributes.get("python_requires").get("solution")
            )
            LOG.log(issue.get_logging_level(), issue.error_str())

            issues.append(issue)
            if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH: setup_valid = False
        elif not parsed_attr:
            issue = SDKValidateIssue(
                "python version not set",
                attributes.get("python_requires").get("missing_msg"),
                severity=attributes.get("python_requires").get("sev"),
                solution=attributes.get("python_requires").get("solution")
            )
            LOG.log(issue.get_logging_level(), issue.error_str())

            issues.append(issue)
            if issue.severity == SDKValidateIssue.SEVERITY_LEVEL_HIGH: setup_valid = False
        else:
            pass # TODO: deal with success

        # TODO: ENTRY_POINTS parse

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
