#!/usr/bin/env python

import warnings
from pkg_resources import resource_string

__version__ = resource_string("resilient", "version.txt").strip()

from resilient import *

warnings.warn("The 'co3' module is deprecated, use 'resilient' instead", DeprecationWarning)
