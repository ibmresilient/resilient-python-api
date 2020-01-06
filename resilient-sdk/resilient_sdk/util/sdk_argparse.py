#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from argparse import ArgumentParser, HelpFormatter
from resilient_sdk.util.sdk_exception import SDKException


class SDKArgumentParser(ArgumentParser):
    """
    Use this class to override the default error method.
    The default raises a custom message and exits.
    We pass the message to an SDKException, so we can catch
    and handle manually
    """
    def error(self, message):
        raise SDKException(message)


class SDKArgHelpFormatter(HelpFormatter):
    """
    Use this class to override the default argparse formatter.
    """

    def __init__(self, prog):
        super(SDKArgHelpFormatter, self).__init__(prog)

    def _format_action_invocation(self, action):
        """
        Overrides how args get printed with -h.
        Remove 'unnecessary' text in the output.
        This looks cleaner
        """

        # For positionals
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        # For optionals
        return ", ".join(action.option_strings)
