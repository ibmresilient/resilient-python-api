#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

"""Global accessor for the Resilient REST API"""

import logging
from threading import Lock

from cachetools import LRUCache, cached
from resilient_circuits import constants

import resilient
from resilient import SimpleHTTPException
from resilient import constants as res_constants

LOG = logging.getLogger(__name__)

# the use case here is to support many different clients
# in the same threaded application. for the most part this
# will be used for just one rest client, so I wanted to keep
# the size reasonably small, while still meeting that use case;
# 256 seems like a reasonable size
CACHE_SIZE = 256
CACHE = LRUCache(maxsize=CACHE_SIZE)
CACHE_LOCK = Lock()

def reset_resilient_client(opts=None):
    """Reset the cached client if the options match or else clear the whole cache"""
    # need to check get_resilient_client.cache_key(opts) against cache since that
    # is the way to access the hash key used in the @cached decorator
    # read more here https://cachetools.readthedocs.io/en/latest/#cachetools.cached
    # to learn about the @cached decorator properties exposed and the use of locks
    # though for 3.6 and 2.7 compatibility, we have to use the CHACHE and CHACHE_LOCK
    # objects directly. for future consideration, see the link above for how to
    # use the objects from the wrapped function
    if opts and _client_cache_key(opts) in CACHE:
        with CACHE_LOCK:
            CACHE.pop(_client_cache_key(opts), None)
    else:
        # brute force clear for some cases where opts aren't given or
        # we want to fully reset the whole cache.
        # this means next time a client is requested, it will
        # be created from scratch -- that's ok
        with CACHE_LOCK:
            CACHE.clear()


def _client_cache_key(opts, *_, **__):
    return (opts.get("cafile"),
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


@cached(CACHE, key=_client_cache_key, lock=CACHE_LOCK)
def get_resilient_client(opts, log_version=True):
    """
    Get a connected instance of :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
    for the SOAR REST API.

    Uses a cache to hold the client in case it has been created before. This is due to the
    nature of this method being used repeatedly within ResilientComponent objects.
    The cache is based on the configuration details. See ``_client_cache_key`` for the hash.
    ``reset_resilient_client`` is used to reset the specific client or the cache as a whole.

    Passes the custom header of ``Resilient-Circuits-Version: 45.0.0`` to the
    :class:`resilient.SimpleClient <resilient.co3.SimpleClient>` instantiation

    :param opts: the connection options - usually the contents of the app.config file
    :type opts: dict
    :param log_version: whether to log the version or not
                        (useful for repeated tests where the version info would clog the logs)
                        defaults to True
    :type log_version: bool

    :return: a connected and verified instance of :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
    """

    custom_headers = {
        constants.HEADER_CIRCUITS_VER_KEY: constants.HEADER_CIRCUITS_VER_VALUE
    }

    retry_args = {
        res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES: opts.get(res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES),
        res_constants.APP_CONFIG_REQUEST_MAX_RETRIES: opts.get(res_constants.APP_CONFIG_REQUEST_MAX_RETRIES),
        res_constants.APP_CONFIG_REQUEST_RETRY_DELAY: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_DELAY),
        res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF: opts.get(res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF)
    }

    resilient_client = resilient.get_client(opts, custom_headers=custom_headers, **retry_args)

    server_version = get_resilient_server_version(resilient_client)

    if log_version:
        LOG.info("IBM Security QRadar SOAR version: v%s", server_version)

    return resilient_client

def get_resilient_server_version(res_client):
    """
    Uses get_const to get the "server_version"
    and gets the ``version`` attribute to print out on startup

    :param res_client: required for communication back to SOAR
    :type res_client: resilient.get_client()
    :return: the server_version ``version`` attribute
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
