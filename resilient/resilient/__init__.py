#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

try:
    from importlib.metadata import distribution, PackageNotFoundError
except ImportError:
    from importlib_metadata import distribution, PackageNotFoundError
try:
    __version__ = distribution(__name__).version
except PackageNotFoundError:
    __version__ = None

from .co3 import SimpleClient, \
    SimpleHTTPException, \
    PatchConflictException, \
    get_client, \
    get_config_file, \
    get_resilient_circuits_version

from .helpers import is_env_proxies_set, get_and_parse_proxy_env_var

from .co3base import ensure_unicode, \
    get_proxy_dict, \
    BasicHTTPException, \
    RetryHTTPException, \
    NoChange
from .co3argparse import parse_parameters, ArgumentParser
from .co3sslutil import match_hostname
from .patch import Patch
from .patch import PatchStatus

from .definitions import (Definition,
                          TypeDefinition,
                          MessageDestinationDefinition,
                          FunctionDefinition,
                          ActionDefinition,
                          ImportDefinition)
