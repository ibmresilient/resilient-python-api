# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Utility functions for configuration"""

from __future__ import print_function
import logging
import pkg_resources


LOG = logging.getLogger("__name__")


def get_config_data(package):
    """Read the default configuration-data section from the given package"""
    data = None
    try:
        dist = pkg_resources.get_distribution(package)
        entries = pkg_resources.get_entry_map(dist, "resilient.circuits.configsection")
        if entries:
            entry = next(iter(entries))
            func = entries[entry].load()
            data = func()
    except pkg_resources.DistributionNotFound:
        pass
    return data or ""
