#!/usr/bin/env python

from pkg_resources import resource_string

__version__ = resource_string("resilient", "version.txt").strip()

from resilient import *

