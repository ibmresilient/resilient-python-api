# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use

class IntegrationError(Exception):
    """
    Class used to signal Integration Errors. It doesn't add any specific information other than
    identifying the type of error

    .. code-block:: python

        from resilient_lib import IntegrationError

        raise IntegrationError("Example raising custom error")

    """

    def __init__(self, value):
        self.value = value

        # Add a __qualname__ attribute if does not exist - needed for PY27 retry
        if not hasattr(IntegrationError, "__qualname__"):
            setattr(IntegrationError, "__qualname__", IntegrationError.__name__)


    def __str__(self):
        return repr(self.value)
