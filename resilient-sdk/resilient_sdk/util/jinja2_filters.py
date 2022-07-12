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


def _dot_py(val):
    """
    Return a value with code quotes around any .py file
      e.g.: sub any string "file.py" to "`file.py`"
    """
    return re.sub(r"([0-9a-z_]+\-*\.py)", r"`\1`", val)


def _scrub_ansi(val):
    """
    Return a value with all all ansi color codes removed
    """
    return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", r"", val) 


def _convert_to_code(val):
    """
    Convert ' to code(`) or ''' code blocks(```) and convert ' within code blocks to "
      e.g.: 'display_name' converts to `display_name`
      e.g.: '''pip install -U 'resilient-circuits'''' converts to
            ```shell
            $ pip install -U "resilient-circuits"
            ```
    """
    return re.sub(r"'{3}(.*)'(.*)'(.*)'{3}", r'\n\n```shell\n$ \1"\2"\3\n```\n', val).replace("'", "`").replace("\t\t", "\t")


def _defaults_to_code(val):
    """
    Make sure that any defaults that are surrounded by << >>  are in code quotes so that they render properly.
      e.g.: <<display_name>> converts to '<<display_name>>'
    """
    return re.sub(r"(<{2}.*>{2})", r"`\1`", val)


def _render_diff(val):
    """
    Renders any diff objects correctly. Assumes that diffs are embedded in strings
    by two tabs before them (only used so far in package files issues' descriptions)
    """
    return re.sub(r"(\t\t.*)(\n+)", r"```diff\n\1\n```", val, flags=re.S).replace("\t", "")


def _readable_time_from_timestamp(val):
    """Assuming val is a %Y%m%d%H%M%S timestamp, produce a readable Y-M-D H-M-S format"""
    if len(val) != 14:
        return val
    return "{0}/{1}/{2} {3}:{4}:{5}".format(val[:4], val[4:6], val[6:8], val[8:10], val[10:12], val[12:])


JINJA_FILTERS = {
    "base64": _filter_base64,
    "camel": _filter_camel,
    "dot_py": _dot_py,
    "scrub_ansi": _scrub_ansi,
    "code": _convert_to_code,
    "defaults": _defaults_to_code,
    "is_dict": lambda x: isinstance(x, dict),
    "diff": _render_diff,
    "datetime": _readable_time_from_timestamp
}


def add_filters_to_jinja_env(env):
    """
    Update the Jinja Environment Filters dict with JINJA_FILTERS
    :param env: Jinja Environment
    """
    env.filters.update(JINJA_FILTERS)

