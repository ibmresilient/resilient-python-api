#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

""" Implementation of `resilient-sdk validate` """

import logging
from resilient import ensure_unicode
from resilient_sdk.cmds.base_cmd import BaseCmd
from resilient_sdk.util.sdk_exception import SDKException
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

        self._print_package_details(args)

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
        cls._validate(args)
        cls._run_tests(args)

    @staticmethod
    def _print_package_details(args):
        """
        TODO
        """
        LOG.info("{0}Printing details{0}".format(sdk_helpers.LOG_DIVIDER))

    @staticmethod
    def _validate(args):
        """
        TODO
        """
        LOG.info("{0}Validating{0}".format(sdk_helpers.LOG_DIVIDER))

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
