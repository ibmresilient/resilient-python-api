#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Custom Jinja2 Filters"""

import sys
import json
import re
from jinja2 import Undefined

if sys.version_info.major < 3:
    # Handle PY 2 specific imports
    from base64 import encodestring as b64encode
else:
    # Handle PY 3 specific imports
    from base64 import encodebytes as b64encode


def _filter_base64(val):
    """
    Return val as base64 encoded string
    """
    if isinstance(val, Undefined):
        return ""
    s = json.dumps(val).encode("utf-8")
    return b64encode(s).decode("utf-8")


def _filter_camel(val):
    """Return CamelCase
       e.g.: "a#bc_def" would convert to "ABcDef"
    """
    titlecase = val.title()
    return re.sub(pattern=r"[\W^_]", repl="", string=titlecase)


JINJA_FILTERS = {
    "base64": _filter_base64,
    "camel": _filter_camel
}


def add_filters_to_jinja_env(env):
    """
    Update the Jinja Environment Filters dict with JINJA_FILTERS
    :param env: Jinja Environment
    """
    env.filters.update(JINJA_FILTERS)
