#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" Implementation of `resilient-sdk validate` """


import logging
import os
import re
from collections import defaultdict

from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util import constants
from resilient_sdk.util import jinja2_filters as jinja_filters
from resilient_sdk.util import package_file_helpers as package_helpers
from resilient_sdk.util import sdk_helpers
from resilient_sdk.util import \
    sdk_validate_configs as validation_configurations
from resilient_sdk.util.sdk_exception import SDKException
from resilient_sdk.util.sdk_validate_issue import SDKValidateIssue

# Get the same logger object that is used in app.py
LOG = logging.getLogger(constants.LOGGER_NAME)

SUB_CMD_VALIDATE = ("--validate", )
SUB_CMD_TESTS = ("--tests", )
SUB_CMD_PYLINT = ("--pylint", )
SUB_CMD_BANDIT = ("--bandit", )
SUB_CMD_SELFTEST = ("--selftest", )
SUB_CMD_TOX_ARGS = ("--tox-args", )


# optional parameters are skipped if they aren't included in the setup.py
SETUP_OPTIONAL_ATTRS = ("python_requires", "author_email")


class CmdValidate(BaseCmd):
    """TODO Docstring"""

    CMD_NAME = "validate"
    CMD_HELP = "Tests the content of all files associated with the app, including code, before packaging it. Only Python >= 3.6 supported."
    CMD_USAGE = """
    $ resilient-sdk validate -p <name_of_package>
    $ resilient-sdk validate -p <name_of_package> -c '/usr/custom_app.config'
    $ resilient-sdk validate -p <name_of_package> --validate
    $ resilient-sdk validate -p <name_of_package> --tests
    $ resilient-sdk validate -p <name_of_package> --tests --tox-args resilient_password="secret_pwd" resilient_host="ibmsoar.example.com"
    $ resilient-sdk validate -p <name_of_package> --tests --settings <path_to_custom_sdk_settings_file>
    $ resilient-sdk validate -p <name_of_package> --pylint --bandit --selftest"""
    CMD_DESCRIPTION = CMD_HELP
    CMD_ADD_PARSERS = ["app_config_parser", constants.SDK_SETTINGS_PARSER_NAME]

    VALIDATE_ISSUES = {}
    SUMMARY_LIST = []

    def setup(self):
        # Define codegen usage and description
        self.parser.usage = self.CMD_USAGE
        self.parser.description = self.CMD_DESCRIPTION
        
        # output not suppressed by default
        self.output_suppressed = False

        # Add any positional or optional arguments here
        self.parser.add_argument(constants.SUB_CMD_OPT_PACKAGE[1], constants.SUB_CMD_OPT_PACKAGE[0],
                                 type=ensure_unicode,
                                 required=False,
                                 help="Path to existing package. Defaults to current directory",
                                 default=os.getcwd())

        self.parser.add_argument(SUB_CMD_VALIDATE[0],
                                 action="store_true",
                                 help="Run validation on package files. No dynamic checks.")

        self.parser.add_argument(SUB_CMD_TESTS[0],
                                 action="store_true",
                                 help="Run tests using package's tox.ini file in a Python 3.6 environment (if 'tox' is installed and tox tests are configured for the package)")

        self.parser.add_argument(SUB_CMD_PYLINT[0],
                                 action="store_true",
                                 help="Run a pylint scan of all .py files under package directory. 'pylint' must be installed)")

        self.parser.add_argument(SUB_CMD_BANDIT[0],
                                 action="store_true",
                                 help="Run a bandit scan of all .py files under package directory. 'bandit' must be installed)")

        self.parser.add_argument(SUB_CMD_SELFTEST[0],
                                 action="store_true",
                                 help="Validate and run the selftest.py file in the package directory. 'resilient-circuits' and the package must be installed in Python environment)")

        self.parser.add_argument(SUB_CMD_TOX_ARGS[0],
                                 nargs="*",
                                 help="""Pytest arguments to pass to tox when validating tests. Format is <attr1>="<value>". Example: '--tox-args my_arg1="value1" my_arg2="value2"'""")

    def execute_command(self, args, output_suppressed=False, run_from_package=False):
        """
        Runs validate. Can be any of: 
          - static validation,
          - selftest,
          - tox tests,
          - pylint,
          - bandit

        If ``run_from_package`` then the validation is being run from ``resilient-sdk package`` command.
        Returns the path to the validation report that was last generated
        """

        # set the appropriate command for error messages
        if not run_from_package:
            SDKException.command_ran = "{0}".format(self.CMD_NAME)

        # Check if Python >= MIN_SUPPORTED_PY_VERSION
        if not sdk_helpers.is_python_min_supported_version(constants.ERROR_WRONG_PYTHON_VERSION):
            raise SDKException(constants.ERROR_WRONG_PYTHON_VERSION)

        sdk_helpers.is_python_min_supported_version()

        self.output_suppressed = output_suppressed

        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Running validate on '{1}'".format(
            constants.LOG_DIVIDER, os.path.abspath(args.package)
        ))
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "Running with '{3}={1}', timestamp: {2}{0}".format(
            constants.LOG_DIVIDER, sdk_helpers.get_resilient_sdk_version(),
            sdk_helpers.get_timestamp(), constants.SDK_PACKAGE_NAME
        ))

        self._print_package_details(args)

        # validate that the given path to the sdk settings is valid
        try:
            sdk_helpers.validate_file_paths(os.R_OK, args.settings)
        except SDKException:
            args.settings = None
            self._log(constants.VALIDATE_LOG_LEVEL_WARNING, "Given path to SDK Settings is either not valid or not readable. Using defaults")

        if run_from_package:
            self._run_main_validation(args, )

        if not run_from_package and not args.validate and not args.tests and not args.pylint and not args.bandit and not args.selftest:
            SDKException.command_ran = "{0} {1} | {2}".format(self.CMD_NAME, constants.SUB_CMD_OPT_PACKAGE[0], constants.SUB_CMD_OPT_PACKAGE[1])
            self._run_main_validation(args, )

        if not run_from_package and args.validate:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_VALIDATE[0])
            self._validate(args, )

        if not run_from_package and args.tests:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_TESTS[0])
            self._run_tests(args, )

        if not run_from_package and args.pylint:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_PYLINT[0])
            self._run_pylint_scan(args, )

        if not run_from_package and args.bandit:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_BANDIT[0])
            self._run_bandit_scan(args, )

        if not run_from_package and args.selftest:
            SDKException.command_ran = "{0} {1}".format(self.CMD_NAME, SUB_CMD_SELFTEST[0])
            self._run_selftest(args, )

        self._print_summary()
        path_report = self._generate_report(self.VALIDATE_ISSUES, args, self._get_counts())

        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "\nSee the detailed report at {0}".format(path_report))


        return path_report

    def _run_main_validation(self, args):
        """
        TODO: docstring, unit tests
        """
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Running main validation{0}".format(constants.LOG_DIVIDER))
        self._validate(args)
        self._run_selftest(args)
        self._run_tests(args)
        self._run_pylint_scan(args)
        self._run_bandit_scan(args)


    def _print_package_details(self, args):
        """
        Print to the console the package details of the specified package
        including:
        - the absolute path of the package
        - display name of the package
        - name of the package
        - version of the package
        - version of SOAR the app was developed against
        - the python dependencies the app has
        - the description of the package
        - the name and email address of the developer
        - if the package supports resilient-circuits>=42.0, indicating that it is proxy supported or not

        :param args: command line args
        :type args: dict
        :return: None - adds list for VALIDATE_ISSUES["details"] in format [{attr1: attr_value}, {...: ...}, ...]
        :rtype: None
        """
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Printing details{0}".format(constants.LOG_DIVIDER))

        # list of tuples for output
        package_details_output = []
        # skips are skipped in non-DEBUG outputs as they are all considered too
        # long for normal output
        skips = ("long_description", "entry_points")

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        self._log(constants.VALIDATE_LOG_LEVEL_DEBUG, "Path to project: {0}".format(path_package))

        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)
        # Generate path to setup.py file + validate we have permissions to read it
        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)



        # parse all supported attributes from setup.py
        parsed_setup_file = package_helpers.parse_setup_py(path_setup_py_file, package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES)

        # check through setup.py file parse 
        # (including values that are in 'skips' here, though they will not be output at the end of this method)
        for attr in package_helpers.SUPPORTED_SETUP_PY_ATTRIBUTE_NAMES:
            attr_val = parsed_setup_file.get(attr)

            # optional parameters are skipped if their values aren't found
            if attr_val or attr not in SETUP_OPTIONAL_ATTRS:
                package_details_output.append((attr, attr_val if attr_val else "**NOT FOUND**"))



        # parse import definition from export.res file or from customize.py (deprecated)
        # package_helpers.get_import_definition_from_customize_py will raise an SDKException if there is an error
        # getting the customize.py file or the import definition from that file
        # we catch this error and output a message that the customize.py file was not correctly found
        try:
            path_customize_py = os.path.join(path_package, parsed_setup_file.get("name"), package_helpers.PATH_CUSTOMIZE_PY)
            sdk_helpers.validate_file_paths(os.R_OK, path_customize_py)
            import_definition = package_helpers.get_import_definition_from_customize_py(path_customize_py)
            if import_definition.get("server_version", {}).get("version"):
                package_details_output.append(("SOAR version", import_definition.get("server_version").get("version")))
            else:
                package_details_output.append(("SOAR version", "Not specified in 'util/data/export.res'. Reload code to make sure server_version is set."))
        except SDKException:
            package_details_output.append(("SOAR version", "**NOT FOUND**; customize.py file not found in {0}".format(path_customize_py)))



        # proxy support is determined by the version of resilient-circuits that is installed
        # if version 42 or greater, proxies are supported
        proxy_supported = False
        install_requires = parsed_setup_file.get(constants.SETUP_PY_INSTALL_REQ_NAME, [])
        # try to parse 'resilient-circuits' from install requires
        package = package_helpers.get_dependency_from_install_requires(install_requires, constants.CIRCUITS_PACKAGE_NAME)

        if package:
            circuits_version = re.findall(r"[0-9]+", package)
            circuits_version = tuple([int(i) for i in circuits_version])

            if circuits_version >= constants.RESILIENT_VERSION_WITH_PROXY_SUPPORT:
                package_details_output.append(("Proxy support", "Proxies supported if running on AppHost>=1.6"))
                proxy_supported = True
        if not proxy_supported:
            package_details_output.append(("Proxy support", "Proxies not fully supported unless running on AppHost>=1.6 and resilient-circuits>=42.0.0"))



        # print output
        for attr, val in package_details_output:
            if attr not in skips:
                level = constants.VALIDATE_LOG_LEVEL_INFO
            else:
                level = constants.VALIDATE_LOG_LEVEL_DEBUG
            self._log(level, u"{0}: {1}".format(attr, val))



        # append details to VALIDATE_ISSUES["details"]
        # details don't count toward final counts so they don't get
        # appended to SUMMARY_LIST
        self.VALIDATE_ISSUES["details"] = package_details_output

    def _validate(self, args):
        """
        Run static validations.
        Wrapper method that validates the contents of the following files in the package dir (all called in separate submethods):
        - setup.py - done in _validate_setup()
        - MANIFEST.in - done in _validate_package_files()
        - apikey_permissions.txt - done in _validate_package_files()
        - entrypoint.sh - done in _validate_package_files()
        - Dockerfile - done in _validate_package_files()
        - fn_package/util/config.py - done in _validate_package_files()
        - fn_package/util/customize.py - done in _validate_package_files()
        - README.md - done in _validate_package_files()
        - fn_package/LICENSE - done in _validate_package_files()
        - fn_package/icons - done in _validate_package_files()
        - fn_package/payload_samples/<fn_function>/... - done in _validate_payload_samples()

        :param args: command line args
        :type args: argparse.ArgumentParser
        :raise SDKException: if the path to the package or required file is not found
        :return: None
        :rtype: None
        """

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)
        self._log(constants.VALIDATE_LOG_LEVEL_DEBUG, "Path to project: {0}".format(path_package))


        # list of ("<file_name>", <validation_function>)
        # this list gets looped and each sub method is ran to check if file is valid
        validations = [
            ("setup.py", self._validate_setup),
            ("package files", self._validate_package_files),
            ("payload samples", self._validate_payload_samples),
        ]


        # loop through files and their associated validation functions
        for file_name, validation_func in validations:
            self._log(constants.VALIDATE_LOG_LEVEL_INFO, u"{0}Validating {1}{0}".format(constants.LOG_DIVIDER, file_name))

            # validate given file using static helper method
            file_valid, issues = validation_func(path_package)
            self.VALIDATE_ISSUES[file_name] = issues
            self.SUMMARY_LIST += issues

            # log output from validation
            for issue in issues:
                self._log(issue.get_logging_level(), issue.error_str())

            self._print_status(constants.VALIDATE_LOG_LEVEL_INFO, file_name, file_valid)


    @staticmethod
    def _validate_setup(path_package):
        """
        Validate the contents of the setup.py file in the given package.
        Builds a list of SDKValidateIssue that describes the status of setup.py

        Uses the sdk_validate_configs.py util file to define the following checks:
        - CRITICAL: Check the file exists
        - CRITICAL: name: is all lowercase and only special char allowed is underscore
        - WARN: display_name: check does not start with <<
        - CRITICAL: license: check does not start with << or is none of any of the GPLs
        - CRITICAL: author: does not start with <<
        - CRITICAL: author_email: does not include "@example.com"
        - CRITICAL: description: does start with default "Resilient Circuits Components"
        - CRITICAL: long_description: does start with default "Resilient Circuits Components"
        - CRITICAL: install_requires: includes resilient_circuits or resilient-circuits at a minimum
        - WARN: checks if exists and WARNS the user if not "python_requires='>=3.6'"
        - CRITICAL: entry_points: that .configsection, .customize, .selftest

        :param path_package: path to package
        :type path_package: str
        :return: Returns boolean value of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool, list[SDKValidateIssue])
        """
        
        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if setup passes validation
        setup_valid = True



        # Generate path to setup.py file + validate we have permissions to read it
        path_setup_py_file = os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY)
        sdk_helpers.validate_file_paths(os.R_OK, path_setup_py_file)
        LOG.debug("setup.py file found at path {0}\n".format(path_setup_py_file))



        attributes = validation_configurations.setup_py_attributes

        # check through setup.py file parse
        for attr, attr_dict in attributes:

            # get output details from attr_dict (to be modified as necessary based on results)
            fail_func = attr_dict.get("fail_func")
            severity = attr_dict.get("severity")
            fail_msg = attr_dict.get("fail_msg")
            missing_msg = attr_dict.get("missing_msg")
            solution = attr_dict.get("solution")

            # run given parsing function
            parsed_attr = attr_dict.get("parse_func")(path_setup_py_file, [attr]).get(attr)

            # check if attr is missing from setup.py file
            if not parsed_attr:
                # if attr isn't found and it is optional, skip to the next attr
                if attr in SETUP_OPTIONAL_ATTRS:
                    continue

                # if missing_msg wasn't provided, this attr can be skipped if not found
                # currently this is used to remove duplicate errors i.e. an attribute
                # is checked twice, so on the second one we skip the handling of it not being found
                if not missing_msg:
                    continue
                
                name = "{0} not found".format(attr)
                description = missing_msg.format(attr)
            else:
                # certain checks require the path to the setup.py
                # file which needs to be passed from here
                include_setup_path = attr_dict.get("include_setup_py_path_in_fail_func", False)

                if include_setup_path:
                    fail = fail_func(parsed_attr, path_setup_py_file)
                else:
                    fail = fail_func(parsed_attr)

                if fail: # check if it fails the 'fail_func'
                    formats = [attr, parsed_attr]

                    # some attr require a supplemental lambda function to properly output their failure message
                    if attr_dict.get("fail_msg_lambda_supplement"):
                        formats.append(attr_dict.get("fail_msg_lambda_supplement")(parsed_attr))

                    name = "invalid value in setup.py"
                    description = fail_msg.format(*formats)
                else: # else is present and did not fail
                    # passes checks
                    name = u"{0} valid in setup.py".format(attr)
                    description = u"'{0}' passed".format(attr)
                    severity = SDKValidateIssue.SEVERITY_LEVEL_DEBUG
                    solution = u"Value found for '{0}' in setup.py: '{1}'"

            # for each attr create a SDKValidateIssue to be appended to the issues list
            issue = SDKValidateIssue(
                name,
                description,
                severity=severity,
                solution=solution.format(attr, parsed_attr)
            )

            issues.append(issue)

        issues.sort()

        # determine if setup validation has failed
        # the any method will short circuit once the condition evaluates to true at least once
        # and then flip the value to indicate whether or not the validation passed
        setup_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)
        
        return setup_valid, issues

    @staticmethod
    def _validate_package_files(path_package):
        """
        Validate the contents of the following files:
        - apikey_permissions.txt
        - MANIFEST.in
        - Dockerfile
        - entrypoint.sh
        - config.py
        - customize.py
        - app and company logos
        - README
        - LICENSE
        
        It validates first that each file exists.
        If the file doesn't exist, issue with CRITICAL is created
        If the file exists, check the validation of that given file by running the given "func" for it

        :param path_package: path to package
        :type path_package: str
        :return: Returns boolean value of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool, list[SDKValidateIssue])
        """
        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if package_files passes validation
        package_files_valid = True


        # get package name and package version
        parsed_setup = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["name", "version"])
        package_name = parsed_setup.get("name")
        package_version = parsed_setup.get("version")

        attributes = validation_configurations.package_files

        for filename,attr_dict in attributes:

            # if a specific path is required for this file, it will be specified in the "path" attribute
            if attr_dict.get("path"):
                path_file = os.path.join(path_package, attr_dict.get("path").format(package_name))
            else:
                # otherwise the file is in root package directory
                path_file = os.path.join(path_package, filename)

            # check that the file exists
            try: 
                sdk_helpers.validate_file_paths(os.R_OK, path_file)
                LOG.debug("{0} file found at path {1}\n".format(filename, path_file))
            except SDKException:
                # file not found: create issue with given "missing_..." info included
                # note that width and height are taken for the missing solution, however,
                # are only used when a logo is missing; the value should be None otherwise
                # be aware of this if a dev ever wants to add infomation to the missing 
                # solution for other package files

                if not attr_dict.get("missing_msg"):
                    continue

                issue_list = [SDKValidateIssue(
                    name=attr_dict.get("name"),
                    description=attr_dict.get("missing_msg").format(path_file),
                    severity=attr_dict.get("missing_severity"),
                    solution=attr_dict.get("missing_solution").format(path_package, attr_dict.get("width"), attr_dict.get("height"))
                )]
            else: # SDKException wasn't caught -- the file exists!

                # make sure the "func" param is specified
                if not attr_dict.get("func"):
                    raise SDKException("'func' not defined in attr_dict={0}".format(attr_dict))

                    
                # run given "func"
                issue_list = attr_dict.get("func")(
                    filename=filename,
                    attr_dict=attr_dict,
                    package_version=package_version,
                    package_name=package_name,
                    path_file=path_file,
                    path_package=path_package
                )

            issues.extend(issue_list)


        # sort and look for and invalid issues
        issues.sort()
        package_files_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return package_files_valid, issues

    @staticmethod
    def _validate_payload_samples(path_package):
        """
        Validate the contents of the output_json_example.json and output_json_schema.json
        files for each function in a package. The payload samples are generated (empty) by codegen
        and can be populated manually or automatically with codegen --gather-results.

        This check is part of the --validate sub-functionality

        :param path_package: path to package
        :type path_package: str
        :return: Returns boolean value of whether or not the payload check passed and a sorted list of SDKValidateIssue
        :rtype: (bool, list[SDKValidateIssue])
        """

        # get package name
        parsed_setup = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["name"])
        package_name = parsed_setup.get("name")

        # grab the function and run it
        # this should return a list of issues with all information about the payload samples
        issues = validation_configurations.payload_samples_attributes.get("func")(
            path_package=path_package,
            package_name=package_name,
            attr_dict=validation_configurations.payload_samples_attributes
        )

        # sort and look for and invalid issues
        issues.sort()
        package_files_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return package_files_valid, issues


    @staticmethod
    def _validate_selftest(path_package, path_app_config=None):
        """
        Validate the contents of the selftest.py file in the given package:
        - check if the package resilient-circuits>=42.0.0 is installed on this Python environment 
          and WARN the user that it is not installed, tell them how to get it
        - verify that this package is installed
        - verify that a util/selftest.py file is present
        - verify that unimplemented does not exist in the file
        - run the selftest method

        :param path_package: path to the package
        :type path_package: str
        :param path_app_config: (optional) path to app_config
        :type path_app_config: str
        :return: Returns boolean value of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool, list[SDKValidateIssue])
        """

        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if selftest passes validation
        selftest_valid = True


        # Generate path to selftest.py file + validate we have permissions to read
        # note that file validation happens in the validations list
        package_name = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["name"]).get("name")
        path_selftest_py_file = os.path.join(path_package, package_name, package_helpers.PATH_SELFTEST_PY)
        LOG.debug("selftest.py file found at path {0}\n".format(path_selftest_py_file))


        # run through validations for selftest
        # details of each check can be found in the sdk_validate_configs.py.selftest_attributes
        for attr_dict in validation_configurations.selftest_attributes:
            if not attr_dict.get("func"):
                raise SDKException("'func' not defined in attr_dict={0}".format(attr_dict))
            issue_passes, issue = attr_dict.get("func")(
                attr_dict=attr_dict,
                path_selftest_py_file=path_selftest_py_file,
                package_name=package_name,
                path_package=path_package,
                path_app_config=path_app_config
            )
            issues.append(issue)
            if not issue_passes:
                issues.sort()
                return False, issues


        # sort and look for and invalid issues
        issues.sort()
        selftest_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return selftest_valid, issues

    @staticmethod
    def _validate_tox_tests(path_package, tox_args=None, path_sdk_settings=None):
        """
        Validate tox is installed and then run the unit tests given for the package:
        - check if tox is installed in the python env (INFO if not, package is considered valid without tests)
        - check that tox.ini file is present (INFO if not)
        - check that envlist=py36 (or greater) is present in tox.ini file - py27 not allowed
        - run tests using tox and report back results
          - tox tests for resilient-circuits require some pytest args; these can come three different ways (ordered by precedence in our logic):
          1. did the user pass args using --tox-args flag? if so, use them
          2. if not, is there either a) a value for the --settings flag that gives the path to a valid sdk_settings.json file? or b) if not, does the sdk_settings.json file exist in the default location?
          3. finally, if none of the above, use the defaults defined in constants.TOX_TESTS_DEFAULT_ARGS

        This method introduced the possibility for returning a -1 from a static validation method.
        This allows for the option that a validation was "skipped" as we deem the case when tox is not installed
        or the tox.ini file is not present. This is the value passed to _print_status when the validation is done
        but if the method is clearly a fail or pass, a boolean value can be returned in the first position

        :param path_package: path to the package
        :type path_package: str
        :param tox_args: (optional) list of tox arguments in the format ["attr1='val1'", "attr2='val2'", ...]
        :type tox_args: list[str]
        :param path_sdk_settings: (optional) path to sdk settings file or None
        :type path_sdk_settings: str
        :return: Returns boolean value or int of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool|int, list[SDKValidateIssue])
        """

        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if the tests check passes validation
        tests_valid = True

        for attr_dict in validation_configurations.tests_attributes:
            if not attr_dict.get("func"):
                raise SDKException("'func' not defined in attr_dict={0}".format(attr_dict))

            issue_pass_num, issue = attr_dict.get("func")(
                path_package=path_package,
                attr_dict=attr_dict,
                tox_args=tox_args,
                path_sdk_settings=path_sdk_settings
            )

            issues.append(issue)
            if issue_pass_num <= 0:
                issues.sort()
                return issue_pass_num, issues
            
        # sort and look for and invalid issues
        issues.sort()
        tests_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return tests_valid, issues

    @staticmethod
    def _pylint_scan(path_package, path_sdk_settings=None):
        """
        Validate pylint is installed and then run pylint scan:
        - check if pylint is installed in the python env (INFO if not)
        - run pylint report results

        This method leverages the possibility of returning -1 from a static validation method.
        This, like in validate_tox_tests, indicates a "skipped" validation

        :param path_package: path to the package
        :type path_package: str
        :param path_sdk_settings: (optional) path to sdk settings file or None
        :type path_sdk_settings: str
        :return: Returns boolean value or int of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool|int, list[SDKValidateIssue])
        """

        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if the scan passes validation
        scan_valid = True

        # get package name
        parsed_setup = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["name"])
        package_name = parsed_setup.get("name")

        for attr_dict in validation_configurations.pylint_attributes:
            if not attr_dict.get("func"):
                raise SDKException("'func' not defined in attr_dict={0}".format(attr_dict))

            issue_pass_num, issue = attr_dict.get("func")(
                path_package=path_package,
                attr_dict=attr_dict,
                package_name=package_name,
                path_sdk_settings=path_sdk_settings
            )

            issues.append(issue)
            if issue_pass_num <= 0:
                issues.sort()
                return issue_pass_num, issues
            
        # sort and look for and invalid issues
        issues.sort()
        scan_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return scan_valid, issues

    @staticmethod
    def _bandit_scan(path_package, path_sdk_settings=None):
        """
        Validate bandit is installed and then run bandit scan:
        - check if bandit is installed in the python env (INFO if not)
        - run bandit; report results

        This method leverages the possibility of returning -1 from a static validation method.
        -1, like in validate_tox_tests, indicates a "skipped" validation

        NOTE: bandit scan is only available in python 3

        :param path_package: path to the package
        :type path_package: str
        :param path_sdk_settings: (optional) path to sdk settings file or None
        :type path_sdk_settings: str
        :return: Returns boolean value or int of whether or not the run passed and a sorted list of SDKValidateIssue
        :rtype: (bool|int, list[SDKValidateIssue])
        """

        # empty list of SDKValidateIssues
        issues = []
        # boolean to determine if the bandit scan passes validation
        scan_valid = True

        # get package name
        parsed_setup = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["name"])
        package_name = parsed_setup.get("name")

        for attr_dict in validation_configurations.bandit_attributes:
            if not attr_dict.get("func"):
                raise SDKException("'func' not defined in attr_dict={0}".format(attr_dict))

            issue_pass_num, issue = attr_dict.get("func")(
                path_package=path_package,
                attr_dict=attr_dict,
                package_name=package_name,
                path_sdk_settings=path_sdk_settings
            )

            issues.append(issue)
            if issue_pass_num <= 0:
                issues.sort()
                return issue_pass_num, issues
            
        # sort and look for and invalid issues
        issues.sort()
        scan_valid = not any(issue.severity == SDKValidateIssue.SEVERITY_LEVEL_CRITICAL for issue in issues)

        return scan_valid, issues

    def _run_tests(self, args):
        """
        Validates and executes tox tests (makes use of static validation method _validate_tox_tests)

        Note that this method sets the values for path_sdk_settings and tox_args to a default if they are
        not passed in with their respective --settings or --tox-args flags
        """
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Running tests{0}".format(constants.LOG_DIVIDER))

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)

        # get values for tox args if they exists otherwise set to default
        tox_args = args.tox_args if hasattr(args, "tox_args") else None # default is None

        # check if tox tests installed and run tox if so
        tox_tests_valid_or_skipped, issues = self._validate_tox_tests(path_package, tox_args, args.settings)
        self.VALIDATE_ISSUES["tests"] = issues
        self.SUMMARY_LIST += issues

        for issue in issues:
            self._log(issue.get_logging_level(), issue.error_str())

        self._print_status(constants.VALIDATE_LOG_LEVEL_INFO, "tests", tox_tests_valid_or_skipped)

    def _run_pylint_scan(self, args):
        """
        Runs pylint scan (if pylint installed in pip env) and outputs the results

        Pylint scan can be isolated by passing in the --pylint flag
        """
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Running pylint{0}".format(constants.LOG_DIVIDER))

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)

        # check if pylint installed in env and run pylint scan if so
        pylint_valid_or_skipped, issues = self._pylint_scan(path_package, args.settings)
        self.VALIDATE_ISSUES["pylint"] = issues
        self.SUMMARY_LIST += issues

        for issue in issues:
            self._log(issue.get_logging_level(), issue.error_str())

        self._print_status(constants.VALIDATE_LOG_LEVEL_INFO, "Pylint Scan", pylint_valid_or_skipped)

    def _run_bandit_scan(self, args):
        """
        Runs bandit scan (if bandit installed in pip env) and outputs the results

        Bandit scan can be isolated by passing in the --bandit flag

        NOTE: bandit scan is only available in python >= 3.6
        """

        # Check if Python >= MIN_SUPPORTED_PY_VERSION
        if not sdk_helpers.is_python_min_supported_version("{0}: Bandit Scan".format(constants.ERROR_WRONG_PYTHON_VERSION)):
            return

        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Running Bandit Scan{0}".format(constants.LOG_DIVIDER))

        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)

        # check if bandit installed in env and run bandit scan if so
        bandit_valid_or_skipped, issues = self._bandit_scan(path_package, args.settings)
        self.VALIDATE_ISSUES["bandit"] = issues
        self.SUMMARY_LIST += issues

        for issue in issues:
            self._log(issue.get_logging_level(), issue.error_str())

        self._print_status(constants.VALIDATE_LOG_LEVEL_INFO, "Bandit Scan", bandit_valid_or_skipped)

    def _run_selftest(self, args):
        """
        Validates and executes selftest.py
        """
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Validating selftest.py{0}".format(constants.LOG_DIVIDER))


        # Get absolute path to package
        path_package = os.path.abspath(args.package)
        # Ensure the package directory exists and we have READ access
        sdk_helpers.validate_dir_paths(os.R_OK, path_package)

        # get path to app_config if exists otherwise set to None
        path_app_config = args.config if hasattr(args, "config") else None

        # validate selftest.py and then execute it if valid
        file_valid, issues = self._validate_selftest(path_package, path_app_config)
        self.VALIDATE_ISSUES["selftest.py"] = issues
        self.SUMMARY_LIST += issues

        for issue in issues:
            self._log(issue.get_logging_level(), issue.error_str())

        self._print_status(constants.VALIDATE_LOG_LEVEL_INFO, "selftest.py", file_valid)



    @staticmethod
    def _generate_report(validate_issues_dict, args, counts):
        """
        Generates a markdown report for the validation run.

        Uses the template markdown file at /data/validate/templates/validate_report.md.jinja2
        to render and save a file in the package at /dist/validate_report.md

        :param validate_issues_dict: dictionary of all issues
        :type validate_issues_dict: dict
        :param args: command line args
        :type args: argparse.ArgumentParser
        :param counts: dict of counts for each validate severity
        :type counts: dict
        :return: returns the path to the generated file (including the formatted timestamp)
        :rtype: str
        """

        LOG.debug("{0}Generating report{0}".format(constants.LOG_DIVIDER))

        # establish timestamp and paths
        timestamp = sdk_helpers.get_timestamp()
        path_package = os.path.abspath(args.package)
        path_dist = os.path.join(path_package, package_helpers.BASE_NAME_DIST_DIR)
        path_report = os.path.join(path_package, package_helpers.PATH_VALIDATE_REPORT)

        # collect the display_name from the setup.py file
        parsed_setup = package_helpers.parse_setup_py(os.path.join(path_package, package_helpers.BASE_NAME_SETUP_PY), ["display_name", "name"])
        display_name = parsed_setup.get("display_name") or parsed_setup.get("name")


        # set up jinja env
        jinja_env = sdk_helpers.setup_jinja_env(constants.VALIDATE_TEMPLATE_PATH)

        # define custom jinja filters
        jinja_filters.add_filters_to_jinja_env(jinja_env)

        # Load the Jinja2 Template
        file_template = jinja_env.get_template(constants.VALIDATE_REPORT_TEMPLATE_NAME)

        # filter out any full paths in args
        args = vars(args)
        for arg in args:
            if isinstance(args[arg], str) and os.path.isdir(args[arg]):
                args[arg] = os.path.basename(args[arg])


        # render the markdown file
        rendered_report = file_template.render(
            display_name=display_name,
            sdk_version=sdk_helpers.get_resilient_sdk_version(),
            timestamp=timestamp,
            validate_issues_dict=validate_issues_dict,
            SEVERITY_THRESHOLD=SDKValidateIssue.SEVERITY_LEVEL_INFO,
            args=", ".join(["`{0}`: {1}".format(arg, args[arg]) for arg in args if args[arg]]),
            criticals=counts[SDKValidateIssue.SEVERITY_LEVEL_CRITICAL],
            warnings=counts[SDKValidateIssue.SEVERITY_LEVEL_WARN],
            passes=int(counts[SDKValidateIssue.SEVERITY_LEVEL_INFO]) + int(counts[SDKValidateIssue.SEVERITY_LEVEL_DEBUG])
        )


        # if the dist directory does not exist: create it
        if not os.path.exists(path_dist):
            LOG.debug("Creating dist directory at {0}".format(path_dist))
            os.makedirs(path_dist)

        LOG.debug("Writing report to {0}".format(path_report))


        sdk_helpers.write_file(path_report, rendered_report)

        return path_report


    def _print_summary(self):
        """
        From list of issues, generates a count of issues that are CRITICAL, WARNING, PASS=sum(INFO, DEBUG)
        and outputs in the format:

        ------------------------
        Validation Results
        ------------------------

        Critical Issues:     <counts[critical]>
        Warnings:            <counts[warning]>
        Validations Passed:  <counts[pass]>

        ------------------------

        :param issues_list: list of SDKValidateIssue objects
        :type issues_list: list[SDKValidateIssue]
        :return: None - prints output to console
        :rtype: None
        """
        counts = self._get_counts()
        
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "{0}Validation Results{0}".format(constants.LOG_DIVIDER))
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "Critical Issues: {0:>14}".format(
            package_helpers.color_output(counts[SDKValidateIssue.SEVERITY_LEVEL_CRITICAL], "CRITICAL")
        ))
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "Warnings: {0:>21}".format(package_helpers.color_output(counts[SDKValidateIssue.SEVERITY_LEVEL_WARN], "WARNING")))
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, "Validations Passed: {0:>11}".format(package_helpers.color_output(
            int(counts[SDKValidateIssue.SEVERITY_LEVEL_DEBUG]) + int(counts[SDKValidateIssue.SEVERITY_LEVEL_INFO]), "PASS")
        ))
        self._log(constants.VALIDATE_LOG_LEVEL_INFO, constants.LOG_DIVIDER)

    
    def _get_counts(self):
        counts = {
            SDKValidateIssue.SEVERITY_LEVEL_CRITICAL: 0,
            SDKValidateIssue.SEVERITY_LEVEL_WARN: 0,
            SDKValidateIssue.SEVERITY_LEVEL_INFO: 0,
            SDKValidateIssue.SEVERITY_LEVEL_DEBUG: 0,
        }
        for issue in self.SUMMARY_LIST:
            counts[issue.severity] += 1

        return counts


    def _print_status(self, level, msg, run_pass):
        """
        Class helper method for logging the status of a specific validation with formatting and color added in
        
        :param level: level to log (from constants.VALIDATE_LOG_LEVEL_<level>)
        :type level: str
        :param msg: message to be formatted and printed
        :type msg: str
        :param run_pass: indicates whether or not this specific validation has passed (set to -1 for "SKIPPED")
        :type run_pass: bool or int
        :return: None - outputs to console using self._log
        :rtype: None
        """
        status = "PASS" if int(run_pass) == 1 else "FAIL" if int(run_pass) == 0 else "SKIPPED"
        msg_formatted = "{0}{1} {2}{0}".format(constants.LOG_DIVIDER, msg, status)
        msg_colored = package_helpers.color_output(msg_formatted, status)
        self._log(level, msg_colored)


    def _log(self, level, msg):
        """
        Class wrapper method for cleaner logging calls.
        Makes use of the class variable "output_suppressed" to calculate if validate
        output should be output to the console (allows for silent running in other sdk commands)
        """
        LOG.log(CmdValidate._get_log_level(level, self.output_suppressed), msg)

    @staticmethod
    def _get_log_level(level, output_suppressed=False):
        """
        Returns logging level to use with logger
        
        50=LOG.critical
        40=LOG.error
        30=LOG.warning
        20=LOG.info
        10=LOG.debug

        https://docs.python.org/3.6/library/logging.html#levels

        :param level: string value of DEBUG, INFO, WARNING, or ERROR; this value is used if output_suppressed==False
        :type level: str
        :param output_suppressed: (optional) value to suppress output; designed for use when calling validate 
                                  from another sdk cmd when output is suppressed, DEBUG level is returned
        :type output_suppressed: bool
        :return: value corresponding to the appropriate log level
        :rtype: int
        """
        if output_suppressed:
            return 10

        if not isinstance(level, str):
            return 10

        level = level.upper()

        if level == constants.VALIDATE_LOG_LEVEL_DEBUG:
            return 10
        elif level == constants.VALIDATE_LOG_LEVEL_INFO:
            return 20
        elif level == constants.VALIDATE_LOG_LEVEL_WARNING:
            return 30
        if level == constants.VALIDATE_LOG_LEVEL_ERROR:
            return 40
        if level == constants.VALIDATE_LOG_LEVEL_CRITICAL:
            return 50
        
        # default returns 10==DEBUG
        return 10
