#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

import warnings
try:
    from importlib.metadata import distribution, PackageNotFoundError
except ImportError:
    from importlib_metadata import distribution, PackageNotFoundError
try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    __version__ = None

from resilient import *

warnings.warning("The 'co3' module is deprecated, use 'resilient' instead", DeprecationWarning)
