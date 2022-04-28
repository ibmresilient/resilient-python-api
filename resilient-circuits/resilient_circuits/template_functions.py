#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""Template processing"""

# Jinja template functions
from deprecated import deprecated
from resilient_lib import global_jinja_env as lib_environment
from resilient_lib import render as lib_render
from resilient_lib import render_json as lib_render_json


@deprecated(version='44.1', reason="Use resilient-lib.global_jinja_env")
def environment():
    return lib_environment()


@deprecated(version='44.1', reason="Use resilient-lib.render")
def render(template, data):
    return lib_render(template, data)


@deprecated(version='44.1', reason="Use resilient-lib.render_json")
def render_json(template, data):
    return lib_render_json(template, data)
