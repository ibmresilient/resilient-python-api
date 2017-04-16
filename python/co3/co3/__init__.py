#!/usr/bin/env python

from .__version__ import resilient_version_number

__version__ = resilient_version_number

from .co3 import SimpleClient
from .co3argparse import ArgumentParser
from .co3sslutil import match_hostname