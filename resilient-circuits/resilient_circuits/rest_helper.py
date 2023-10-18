#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Global accessor for the Resilient REST API"""

import logging

from resilient_circuits import constants

import resilient
from resilient import SimpleHTTPException
from resilient import constants as res_constants

LOG = logging.getLogger(__name__)

resilient_client = None
connection_opts = None


def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None


def get_resilient_client(opts):
    """
    Get a connected instance of :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
    for the SOAR REST API

    Passes the custom header of ``Resilient-Circuits-Version: 45.0.0`` to the
    :class:`resilient.SimpleClient <resilient.co3.SimpleClient>` instantiation

    :param opts: the connection options - usually the contents of the app.config file
    :type opts: dict

    :return: a connected and verified instance of :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
    """
    global resilient_client
    global connection_opts

    new_opts = (opts.get("cafile"),
                opts.get("org"),
                opts.get("host"),
                opts.get("port"),
                opts.get("resource_prefix"),
                opts.get("proxy_host"),
                opts.get("proxy_port"),
                opts.get("proxy_user"),
                opts.get("proxy_password"),
                opts.get("email"),
                opts.get("api_key_id"))

    custom_headers = {
        constants.HEADER_CIRCUITS_VER_KEY: constants.HEADER_CIRCUITS_VER_VALUE
    }

    if new_opts != connection_opts:
        resilient_client = None
        connection_opts = new_opts

    if resilient_client:
        return resilient_client

    retry_args = {
        res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES: opts.get(res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES),
        res_constants.APP_CONFIG_REQUEST_MAX_RETRIES: opts.get(res_constants.APP_CONFIG_REQUEST_MAX_RETRIES),
        res_constants.APP_CONFIG_REQUEST_RETRY_DELAY: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_DELAY),
        res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF)
    }

    resilient_client = resilient.get_client(opts, custom_headers=custom_headers, **retry_args)

    server_version = get_resilient_server_version(resilient_client)

    LOG.info("IBM Security QRadar SOAR version: v%s", server_version)

    return resilient_client

def get_resilient_server_version(res_client):
    """
    Uses get_const to get the "server_version"
    and gets the ``version`` attribute to print out on startup

    :param res_client: required for communication back to SOAR
    :type res_client: resilient.get_client()
    :return: the server_version in the form ``major.minor.build_number``
    :rtype: str
    """
    LOG.debug("Getting server version")
    try:
        server_version = res_client.get_const().get("server_version", {})
    except SimpleHTTPException:
        # fine to ignore any exceptions here as this is
        # not critical to get the server info if something goes wrong
        LOG.debug("Failed to retrieve version from SOAR server. Continuing gracefully...")
        server_version = {}

    return server_version.get("version")
