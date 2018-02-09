#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

import warnings
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    __version__ = None

from resilient import *

warnings.warn("The 'co3' module is deprecated, use 'resilient' instead", DeprecationWarning)
