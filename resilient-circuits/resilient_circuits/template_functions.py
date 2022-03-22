#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""Template processing"""

# Jinja template functions

from resilient_lib import environment as lib_environment,\
                render as lib_render,\
                render_json as lib_render_json
from deprecated import deprecated


@deprecated(version='44.1', reason="Use resilent-lib.environment")
def environment():
    return lib_environment()

@deprecated(version='44.1', reason="Use resilent-lib.render")
def render(template, data):
    return lib_render(template, data)

@deprecated(version='44.1', reason="Use resilent-lib.render_json")
def render_json(template, data):
    return lib_render_json(template, data)