#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Global accessor for the Resilient REST API"""

import functools
import logging
import os
import resilient
import time

resilient_client = None
connection_opts = None

MAX_CONNECTION_RETRIES = "max_connection_retries"

def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None


def retry(func):
    """
    added retry logic to a connection
    :return: connection handler upon successful connection
    :raises: OSError
    """
    LOG = logging.getLogger(__name__)

    @functools.wraps(func)
    def wrapper(opts):
        INCR_RESTART_DELAY = 60     # increase wait by 1 minute
        MAX_DELAY = 300             # delay wait will not exceed 5 minutes
        MAX_RETRIES = int(opts.get(MAX_CONNECTION_RETRIES, 1)) # default is current behavior

        restart_delay = 0           # number of seconds to wait
        retry_count = 0             # count the number of times through our loop

        # continue until:
        #  connection is successful, or
        #  retry count is exceeded
        # if MAX_RETRIES = 0, we will wait forever
        while True:
            try:
                return func(opts)
            except OSError as oserr:
                if "Failed to establish a new connection" not in str(oserr):
                    raise OSError(oserr)
                else:
                    retry_count += 1
                    if MAX_RETRIES and retry_count > MAX_RETRIES:
                        raise OSError("Exceeded retries: {}".format(MAX_RETRIES))

                    if restart_delay < MAX_DELAY:
                        restart_delay += INCR_RESTART_DELAY

            LOG.info("Retry %s:%s waiting %s secs for Resilient connection",
                     retry_count,
                     MAX_RETRIES if MAX_RETRIES > 0 else "unlimited",
                     restart_delay)
            time.sleep(restart_delay)

    return wrapper

@retry
def get_resilient_client(opts):
    """Get a connected instance of SimpleClient for Resilient REST API"""
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
    if new_opts != connection_opts:
        resilient_client = None
        connection_opts = new_opts
    if resilient_client:
        return resilient_client

    resilient_client = resilient.get_client(opts)
    return resilient_client
