#!/usr/bin/env python

from pkg_resources import resource_string

__version__ = resource_string(__name__, "version.txt").strip()

from .co3 import SimpleClient, PatchConflictException, NoChange, get_client, get_config_file
from .co3argparse import ArgumentParser
from .co3sslutil import match_hostname
from .patch import Patch
from .patch import PatchStatus

