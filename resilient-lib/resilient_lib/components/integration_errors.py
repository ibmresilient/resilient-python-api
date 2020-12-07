# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

class IntegrationError(Exception):
    """
    Class used to signal Integration Errors. It doesn't add any specific information other than
    identifying the type of error
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
