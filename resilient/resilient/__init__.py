#!/usr/bin/env python

from pkg_resources import resource_string

__version__ = resource_string(__name__, "version.txt").strip()

from .co3 import SimpleClient, SimpleHTTPException, PatchConflictException, NoChange, get_client, get_config_file, ensure_unicode, get_proxy_dict
from .co3argparse import parse_parameters, ArgumentParser
from .co3sslutil import match_hostname
from .patch import Patch
from .patch import PatchStatus

