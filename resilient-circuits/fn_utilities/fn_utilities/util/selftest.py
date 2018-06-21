# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

def _selftest_function():
    """Placeholder for selftest function. An example use would be to test package api connectivity."""
    return { "state": "unimplemented" }