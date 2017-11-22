#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

"""Global accessor for the Resilient REST API"""

import resilient

resilient_client = None
connection_opts = None


def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None


def get_resilient_client(opts):
    """Get a connected instance of SimpleClient for Resilient REST API"""
    global resilient_client
    global connection_opts

    new_opts = (opts.get("cafile"),
                opts.get("org"),
                opts.get("host"),
                opts.get("port"),
                opts.get("proxy_host"),
                opts.get("proxy_port"),
                opts.get("proxy_user"),
                opts.get("proxy_password"),
                opts.get("email"))
    if new_opts != connection_opts:
        resilient_client = None
        connection_opts = new_opts
    if resilient_client:
        return resilient_client

    resilient_client = resilient.get_client(opts)
    return resilient_client
