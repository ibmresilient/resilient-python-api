#!/usr/bin/env python

from pkg_resources import Requirement, resource_filename

with open(resource_filename(Requirement("co3"), "version.txt")) as f:
    __version__ = f.read().strip()

from .co3 import SimpleClient
from .co3argparse import ArgumentParser
from .co3sslutil import match_hostname