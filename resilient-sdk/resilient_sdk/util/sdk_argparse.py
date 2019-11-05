#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

from argparse import ArgumentParser
from resilient_sdk.util.sdk_exception import SDKException


class SDKArgumentParser(ArgumentParser):
    """
    Use this class to overwrite the default error method.
    The default raises a custom message and exits.
    We pass the message to an SDKException, so we can catch
    and handle manually
    """
    def error(self, message):
        raise SDKException(message)
