#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import logging
import os
from threading import Thread
import time
import pkg_resources
from requests.exceptions import ConnectionError, SSLError
from resilient import constants as res_constants
from resilient import BasicHTTPException, SimpleClient, is_env_proxies_set, get_and_parse_proxy_env_var
from resilient_circuits.actions_component import SELFTEST_ERRORS, SELFTEST_SUBSCRIPTIONS
from resilient_circuits.stomp_events import SelftestTerminateEvent
from resilient_circuits import constants, helpers, app

# Get the same logger object that is used for resilient_circuits commands
LOG = logging.getLogger(constants.CMDS_LOGGER_NAME)

ERROR_EXIT_CODES_MAP = {
    20: 20,     # REST: Generic connection error
    401: 21,    # REST: Connection unauthorized
    23: 23,     # REST: SSL Error (Certificate Error)
    30: 30,     # STOMP: Generic connection error
    31: 31,     # STOMP: Not authorized to instansiate STOMP connection
    32: 32,     # STOMP: Not authorized to read from queue
}


def error_connecting_to_soar(host, reason="Unknown", status_code=20):
    """
    Logs the host, reason and error code why it cannot connect to SOAR
    and exits with the error code defined in ERROR_EXIT_CODES_MAP
    """

    # Remove resilient-circuits logging handler
    LOG.parent.handlers = []

    LOG.info("\nERROR: could not connect to SOAR at '{0}'.\nReason: {1}\nError Code: {2}".format(host, reason, ERROR_EXIT_CODES_MAP.get(status_code, 1)))
    exit(ERROR_EXIT_CODES_MAP.get(status_code, 1))


def check_soar_rest_connection(cmd_line_args, app_configs):
    """
    Check if we can  successfully get a resilient_client
    therefore that will tell us if we have configured the app.config
    file correctly in order to establish a connection and authenticate
    with SOAR

    :param cmd_line_args: an argparse.Namespace object containing all command line params
    :type cmd_line_args: argparse.Namespace
    :param app_configs: a dict of all the configurations in the app.config file
    :type app_configs: dict
    :excepts BasicHTTPException: if we cannot authenticate. Exists with 21
    :excepts SSLError: if the cafile that is supplied is invalid. Exits with 23
    :excepts Exception: generic error. Also raises if the user is not a member of the current org. Exits with 20
    :return: Nothing

    """
    LOG.info("{0}Testing REST connection to SOAR{0}".format(constants.LOG_DIVIDER))

    host = app_configs.get("host", constants.DEFAULT_NONE_STR)
    user = app_configs.get("api_key_id", app_configs.get("email", constants.DEFAULT_NONE_STR))
    cafile = app_configs.get("cafile") if app_configs.get("cafile") else ""

    if not os.path.isfile(cafile):
        LOG.warning("- WARNING: No certificate file specified, connection will not be secure")

    LOG.info("- Checking if we can authenticate a REST connection with '{0}' to '{1}'".format(user, host))

    if is_env_proxies_set():
        proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTPS_PROXY)

        if not proxy_details:
            proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTP_PROXY)

        LOG.info("- Using a '{0}' Proxy with Host '{1}' and Port '{2}'".format(proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port")))

    try:
        res_client = helpers.get_resilient_client(ALLOW_UNRECOGNIZED=True)

    except BasicHTTPException as e:
        error_connecting_to_soar(host, e.response.reason, e.response.status_code)

    except SSLError as e:
        error_connecting_to_soar(host, e, 23)

    except ConnectionError as e:
        error_connecting_to_soar(host, e, 20)

    except Exception as e:
        if hasattr(e, "args") and isinstance(e.args, tuple):
            error_connecting_to_soar(host, e, 20)

        error_connecting_to_soar(host, u"Unknown REST Error: {0}".format(e), 20)

    if not isinstance(res_client, SimpleClient):
        error_connecting_to_soar(host, "Unknown REST Error", 20)

    LOG.info("{0}Successfully connected via REST!{0}".format(constants.LOG_DIVIDER))


def check_soar_stomp_connection(cmd_line_args, app_configs):
    """
    TODO
    """
    LOG.info("{0}Testing STOMP connection to SOAR{0}".format(constants.LOG_DIVIDER))

    host = app_configs.get("host", constants.DEFAULT_NONE_STR)
    user = app_configs.get("api_key_id", app_configs.get("email", constants.DEFAULT_NONE_STR))

    LOG.info("- Checking if we can authenticate a STOMP connection with '{0}' to '{1}'".format(user, host))

    try:
        LOG.info("{0}Instantiating instance of resilient-circuits and starting it...{0}".format(constants.LOG_DIVIDER))
        resilient_circuits_instance = app.App(ALLOW_UNRECOGNIZED=True, IS_SELFTEST=True)

        # Create thread that targets the `run()` method of the main resilient_circuits component
        t_running_resilient_circuits = Thread(target=resilient_circuits_instance.run, name="resilient_circuits")
        t_running_resilient_circuits.start()

        start_time = time.time()

        while len(SELFTEST_SUBSCRIPTIONS) == 0:
            LOG.parent.info("- Waiting for subscription to message destination. Sleeping for 2 seconds")
            time.sleep(2)

            if helpers.should_timeout(start_time, app_configs.get(constants.DEFAULT_SELFTEST_TIMEOUT_KEY, constants.DEFAULT_SELFTEST_TIMEOUT_VALUE)):
                resilient_circuits_instance.action_component.fire(SelftestTerminateEvent())
                error_connecting_to_soar(host, "Could not subscribe to any message destinations", 30)

        # Send event to Terminate resilient-circuits
        resilient_circuits_instance.action_component.fire(SelftestTerminateEvent())

        # Remove resilient-circuits logging handler
        time.sleep(2)
        LOG.parent.handlers = []

        if SELFTEST_ERRORS:
            for e in SELFTEST_ERRORS:
                if b"is not authorized to read from queue" in e:
                    error_connecting_to_soar(host, "{0} is not authorized to read from the App's Message Destination".format(host), 32)

            error_connecting_to_soar(host, u"Unknown STOMP Error: {0}".format(e), 30)

    except BasicHTTPException as e:
        error_connecting_to_soar(host, e.response.reason, 32)

    except Exception as e:
        error_connecting_to_soar(host, u"Unknown STOMP Error: {0}".format(e), 30)

    LOG.info("{0}Successfully connected via STOMP!{0}".format(constants.LOG_DIVIDER))


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
    check_soar_stomp_connection(cmd_line_args, app_configs)

    LOG.info("{0}selftest complete{0}".format(constants.LOG_DIVIDER))
