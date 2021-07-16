#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import logging
import os
import pkg_resources
from requests.exceptions import ConnectionError, SSLError
from resilient import constants as res_constants
from resilient import BasicHTTPException, SimpleClient, is_env_proxies_set, get_and_parse_proxy_env_var
from resilient_circuits import constants, helpers


# Get the same logger object that is used for resilient_circuits commands
LOG = logging.getLogger(constants.CMDS_LOGGER_NAME)

ERROR_EXIT_CODES_MAP = {
    20: 20,     # Generic no connection error
    401: 21,    # Connection unauthorized
    23: 23      # SSL Error (Certificate Error)
}


def error_connecting_to_soar_rest(host, reason="Unknown", status_code=20):
    LOG.info("\nERROR: could not connect to SOAR at '{0}'.\nReason: {1}\nError Code: {2}".format(host, reason, ERROR_EXIT_CODES_MAP.get(status_code, 1)))
    exit(ERROR_EXIT_CODES_MAP.get(status_code, 1))


def check_soar_rest_connection(cmd_line_args, app_configs):

    LOG.info("{0}Testing REST connection to SOAR{0}".format(constants.LOG_DIVIDER))

    host = app_configs.get("host", constants.DEFAULT_NONE_STR)
    user = app_configs.get("api_key_id", app_configs.get("email", constants.DEFAULT_NONE_STR))
    cafile = app_configs.get("cafile") if app_configs.get("cafile") else ""

    if not os.path.isfile(cafile):
        LOG.warning("- WARNING: No certificate file specified, connection will not be secure")

    LOG.info("- Checking if we can authenticate '{0}' with '{1}'".format(user, host))

    if is_env_proxies_set():
        proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTPS_PROXY)

        if not proxy_details:
            proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTP_PROXY)

        LOG.info("- Using a '{0}' Proxy with Host '{1}' and Port '{2}'".format(proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port")))

    try:
        res_client = helpers.get_resilient_client(ALLOW_UNRECOGNIZED=True)

    except BasicHTTPException as e:
        error_connecting_to_soar_rest(host, e.response.reason, e.response.status_code)

    except SSLError as e:
        error_connecting_to_soar_rest(host, e, 23)

    except ConnectionError as e:
        error_connecting_to_soar_rest(host, e, 20)

    except Exception as e:
        if hasattr(e, "args") and isinstance(e.args, tuple):
            error_connecting_to_soar_rest(host, e, 20)
        raise e

    if not isinstance(res_client, SimpleClient):
        error_connecting_to_soar_rest(host, "Unknown", 20)

    LOG.info("- Successfully connected!")


def check_soar_stomp_connection(cmd_line_args):
    # TODO
    pass


def run_apps_selftest(cmd_line_args):
    # TODO
    pass


def execute_command(cmd_line_args):
    """
    TODO
    """
    # TODO: get the app name
    LOG.info("{0}Running selftest for <App Name> with IBM SOAR{0}".format(constants.LOG_DIVIDER))

    if hasattr(cmd_line_args, "print_env") and cmd_line_args.print_env:
        LOG.info("- Printing runtime environment")
        LOG.info(helpers.get_env_str(pkg_resources.working_set))

    LOG.info("- Getting app.configs")
    app_configs = helpers.get_configs(ALLOW_UNRECOGNIZED=True)

    check_soar_rest_connection(cmd_line_args, app_configs)
    pass
