# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility functions for configuration"""

from __future__ import print_function
from resilient_circuits.helpers import get_package_function
import logging


LOG = logging.getLogger("__name__")


def get_config_data(package):
    """Read the default configuration-data section from the given package"""

    config_funct = get_package_function(package, "resilient.circuits.configsection")
    return config_funct() if config_funct else None
