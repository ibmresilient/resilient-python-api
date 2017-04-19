#!/usr/bin/env python

from pkg_resources import resource_string

__version__ = resource_string(__name__, "version.txt").strip()

from .co3 import SimpleClient, get_client
from .co3argparse import ArgumentParser
from .co3sslutil import match_hostname

