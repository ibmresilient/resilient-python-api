#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging
import os
import time
from collections import defaultdict
from threading import Thread

import pkg_resources
from requests.exceptions import ConnectionError, SSLError
from resilient import BasicHTTPException, SimpleClient, SimpleHTTPException
from resilient import constants as res_constants
from resilient import get_and_parse_proxy_env_var, is_env_proxies_set
from resilient_circuits import app, constants, helpers
from resilient_circuits.actions_component import (SELFTEST_ERRORS,
                                                  SELFTEST_SUBSCRIPTIONS)
from resilient_circuits.stomp_events import SelftestTerminateEvent

# Get the same logger object that is used for resilient_circuits commands
LOG = logging.getLogger(constants.CMDS_LOGGER_NAME)

ERROR_EXIT_CODES_MAP = {
    1: constants.EXIT_SELFTEST_ERROR,
    2: constants.EXIT_SELFTEST_UNIMPLEMENTED,
    20: constants.EXIT_REST_CONNECTION_ERROR,
    401: constants.EXIT_REST_UNAUTHORIZED,
    22: constants.EXIT_REST_OS_ERROR,
    23: constants.EXIT_REST_SSL_ERROR,
    24: constants.EXIT_REST_ORG_ERROR,
    25: constants.EXIT_REST_INVALID_PW,
    30: constants.EXIT_STOMP_ERROR,
    31: constants.EXIT_STOMP_UNAUTHORIZED_CONN,
    32: constants.EXIT_STOMP_UNAUTHORIZED_Q,
    33: constants.EXIT_STOMP_Q_TIMEOUT
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


def check_pam_plugin_selftest(app_configs):
    """
    Run PAM plugin's 'selftest' function which will check if the plugin
    is properly configured.

    Some plugins may not have a selftest or some app configurations may
    not have a plugin -- in either of those cases, let it go with simply
    a log message.

    In the case the the plugin exists, and has a selftest, run it.
    The function should return a tuple of bool, str where the first
    element is True if the plugin is correctly configured and
    the second element is a reason if it is incorrectly configured.

    :param app_configs: app configs for the app -- should contain a .pam_plugin object
    :type app_configs: ``resilient.app_config.AppConfigManager``
    """
    LOG.info("{0}Testing PAM Plugin details{0}".format(constants.LOG_DIVIDER))

    if not app_configs or not hasattr(app_configs, "pam_plugin") or not app_configs.pam_plugin:
        LOG.info("{0}No Plugin specified. Skipping test{0}".format(constants.LOG_DIVIDER))
        return

    try:
        LOG.info("- Running pam plugin selftest")
        result = app_configs.pam_plugin.selftest()
    except NotImplementedError:
        LOG.warning("{0}PAM Plugin selftest not implemented for custom plugin. Skipping test{0}".format(constants.LOG_DIVIDER))
        return
    except Exception as err:
        LOG.warning("Unknown error while running PAM Plugin selftest: {0}".format(str(err)))
        return

    # result should be a tuple of (bool, str),
    # but in the case that something is improperly implemented,
    # assume that if not a tuple that the result is the bool portion
    # and use that bool and "REASON UNKNOWN"
    if isinstance(result, tuple):
        selftest_pass, reason = result
    else:
        LOG.warning("PAM Plugin selftest did not return the expected tuple. Make sure selftest is properly implemented")
        selftest_pass, reason = (result, "REASON UNKNOWN")

    if not selftest_pass:
        LOG.error("\nERROR: PAM Plugin test failed. Reason: {0}.\nError Code: {1}".format(reason, ERROR_EXIT_CODES_MAP.get(1, 1)))
        exit(ERROR_EXIT_CODES_MAP.get(1, 1))
    else:
        LOG.info("{0}PAM Plugin correctly configured{0}".format(constants.LOG_DIVIDER))

def check_soar_rest_connection(cmd_line_args, app_configs):
    """
    Check if we can  successfully get a resilient_client
    therefore that will tell us if we have configured the app.config
    file correctly in order to establish a REST connection and authenticate
    with SOAR

    :param cmd_line_args: an argparse.Namespace object containing all command line params
    :type cmd_line_args: argparse.Namespace
    :param app_configs: a dict of all the configurations in the app.config file
    :type app_configs: dict
    :excepts BasicHTTPException: if we cannot authenticate. Exits with 21
    :excepts SSLError: if the cafile that is supplied is invalid. Exits with 23
    :excepts Exception: generic error. Also raises if the user is not a member of the current org. Exits with 20
    :return: Nothing

    """
    LOG.info("{0}Testing REST connection to SOAR{0}".format(constants.LOG_DIVIDER))

    host = app_configs.get("host", constants.DEFAULT_NONE_STR)
    user = app_configs.get("api_key_id", app_configs.get("email", constants.DEFAULT_NONE_STR))
    cafile = app_configs.get("cafile") if app_configs.get("cafile") else ""

    if not os.path.isfile(cafile):
        LOG.warning("- WARNING: No certificate file specified. Only allows the connections that are trusted by operating system.")

    LOG.info("- Checking if we can authenticate a REST connection with '{0}' to '{1}'".format(user, host))

    if is_env_proxies_set():
        proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTPS_PROXY)

        if not proxy_details:
            proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTP_PROXY)

        LOG.info("- Using a '{0}' Proxy with Host '{1}' and Port '{2}'".format(proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port")))

    try:
        res_client = helpers.get_resilient_client(ALLOW_UNRECOGNIZED=True)

    except BasicHTTPException as e:
        # Connection unauthorized
        error_connecting_to_soar(host, e.response.reason, e.response.status_code)

    except SimpleHTTPException as e:
        # Incorrect User/Password
        if hasattr(e, "args") and isinstance(e.args, tuple) and constants.ERROR_INVALID_USR in e.args[0]:
            error_connecting_to_soar(host, e, 25)

        error_connecting_to_soar(host, u"Unknown REST Error: {0}".format(e), 20)

    except SSLError as e:
        # SSL Error (Certificate Error)
        error_connecting_to_soar(host, e, 23)

    except ConnectionError as e:
        # Generic connection error
        error_connecting_to_soar(host, e, 20)

    except OSError as e:
        if hasattr(e, "args") and isinstance(e.args, tuple) and constants.ERROR_CA_FILE_NOT_FOUND in e.args[0]:
            # CA file could not be found/read
            error_connecting_to_soar(host, e, 22)

        error_connecting_to_soar(host, u"Unknown REST Error: {0}".format(e), 20)

    except Exception as e:
        # Generic connection error (normally related to the user's org membership)
        if hasattr(e, "args") and isinstance(e.args, tuple):

            # User not member of organization error
            if constants.ERROR_USR_NOT_MEMBER_ORG in e.args[0]:
                error_connecting_to_soar(host, e, 24)

            error_connecting_to_soar(host, e, 20)

        error_connecting_to_soar(host, u"Unknown REST Error: {0}".format(e), 20)

    if not isinstance(res_client, SimpleClient):
        error_connecting_to_soar(host, "Unknown REST Error", 20)

    LOG.info("{0}Successfully connected via REST!{0}".format(constants.LOG_DIVIDER))


def check_soar_stomp_connection(cmd_line_args, app_configs):
    """
    Check if we can successfully start an instance of resilient_circuits
    and therefore that will tell us if we have configured the app.config
    file correctly in order to establish a STOMP connection and authenticate
    with SOAR

    :param cmd_line_args: an argparse.Namespace object containing all command line params
    :type cmd_line_args: argparse.Namespace
    :param app_configs: a dict of all the configurations in the app.config file
    :type app_configs: dict
    :excepts BasicHTTPException: if we cannot authenticate. Exits with 32
    :excepts Exception: generic error. Exits with 30
    :return: Nothing

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

            if helpers.should_timeout(start_time, app_configs.get(constants.APP_CONFIG_SELFTEST_TIMEOUT, constants.DEFAULT_SELFTEST_TIMEOUT_VALUE)):
                resilient_circuits_instance.action_component.fire(SelftestTerminateEvent())
                error_connecting_to_soar(host, "Could not subscribe to any message destinations", 33)

        # Send event to Terminate resilient-circuits
        resilient_circuits_instance.action_component.fire(SelftestTerminateEvent())

        # Remove resilient-circuits logging handler
        time.sleep(2)
        LOG.parent.handlers = []

        if SELFTEST_ERRORS:
            # Not authorized to read from queue
            for e in SELFTEST_ERRORS:
                if b"is not authorized to read from queue" in e:
                    error_connecting_to_soar(host, "'{0}' is not authorized to read from the App's Message Destination".format(helpers.get_user(app_configs)), 32)

            error_connecting_to_soar(host, u"Unknown STOMP Error: {0}".format(e), 30)

    except BasicHTTPException as e:
        # Not authorized to instansiate STOMP connection
        error_connecting_to_soar(host, e.response.reason, 31)

    except Exception as e:
        # Generic connection error
        error_connecting_to_soar(host, u"Unknown STOMP Error: {0}".format(e), 30)

    LOG.info("{0}Successfully connected via STOMP!{0}".format(constants.LOG_DIVIDER))


def run_apps_selftest(cmd_line_args, app_configs):
    """
    loop through every selftest for every eligible package, call and store returned state,
    print out package and their selftest states
    """

    if hasattr(cmd_line_args, "print_env") and cmd_line_args.print_env:
        LOG.info(helpers.get_env_str(pkg_resources.working_set))

    components = defaultdict(list)

    # custom entry_point only for selftest functions
    selftest_entry_points = [ep for ep in pkg_resources.iter_entry_points('resilient.circuits.selftest')]
    for ep in selftest_entry_points:
        components[ep.dist].append(ep)

    if len(selftest_entry_points) == 0:
        LOG.info("No selftest entry points found.")
        return None

    # make a copy
    install_list = list(cmd_line_args.install_list) if cmd_line_args.install_list else []

    # Prepare a count of exceptions found with selftests.
    selftest_failure_count = 0
    selftest_unimplemented_count = 0
    selftest_not_found_count = 0
    selftest_unknown_count = 0

    for dist, component_list in components.items():
        if cmd_line_args.install_list is None or dist.project_name in install_list:
            # remove name from list
            if dist.project_name in install_list:
                install_list.remove(dist.project_name)

            LOG.info("{0}Running selftest for: '{1}'{0}".format(constants.LOG_DIVIDER, dist.project_name))
            # add an entry for the package
            LOG.info("\n%s: ", dist.project_name)
            for ep in component_list:
                # load the entry point
                try:
                    f_selftest = ep.load()
                except ModuleNotFoundError:
                    selftest_not_found_count += 1
                    continue

                try:
                    # f_selftest is the selftest function, we pass the selftest resilient options in case it wants to use it
                    start_time_milliseconds = int(round(time.time() * 1000))

                    status = f_selftest(app_configs)

                    end_time_milliseconds = int(round(time.time() * 1000))

                    delta_milliseconds = end_time_milliseconds - start_time_milliseconds
                    delta_seconds = delta_milliseconds / 1000

                    state = status.get("state")

                    if isinstance(state, str):
                        LOG.info("\t%s: %s\n\tselftest output:\n\t%s\n\tElapsed time: %f seconds", ep.name, state, status, delta_seconds)

                        if state.lower() == constants.SELFTEST_FAILURE_STATE:
                            selftest_failure_count += 1
                        elif state.lower() == constants.SELFTEST_UNIMPLEMENTED_STATE:
                            selftest_unimplemented_count += 1
                        elif state.lower() != constants.SELFTEST_SUCCESS_STATE:
                            selftest_unknown_count += 1

                    else:
                        LOG.info("\t%s:\n\tUnsupported dictionary returned:\n\t%s\n\tElapsed time: %f seconds", ep.name, status, delta_seconds)

                except Exception as e:
                    LOG.error("Error while calling %s. Exception: %s", ep.name, str(e))
                    selftest_failure_count += 1
                    continue

    # any missed packages?
    if install_list:
        LOG.warning("\n%s not found. Selftest not ran for %s. Check package name(s)\n", install_list, install_list)

    # Check if any failures were found and printed to the console
    if selftest_failure_count or selftest_unknown_count:
        LOG.info("\nERROR: running selftest for App.\nError Code: {0}".format(ERROR_EXIT_CODES_MAP.get(1, 1)))
        exit(ERROR_EXIT_CODES_MAP.get(1, 1))
    elif selftest_unimplemented_count:
        LOG.info("\nERROR: selftest is unimplemented for this App. Note: the App may still continue to work...\nError Code: {0}".format(ERROR_EXIT_CODES_MAP.get(2, 2)))
        exit(ERROR_EXIT_CODES_MAP.get(2, 2))
    elif selftest_not_found_count:
        LOG.info("\nERROR: selftest not found for this App. Note: the App may still continue to work...\nError Code: {0}".format(ERROR_EXIT_CODES_MAP.get(2, 2)))
        exit(ERROR_EXIT_CODES_MAP.get(2, 2))

    if not install_list:
        LOG.info("{0}Successfully ran App's selftest!{0}".format(constants.LOG_DIVIDER))


def execute_command(cmd_line_args):
    LOG.info("{0}Running selftest with IBM SOAR{0}".format(constants.LOG_DIVIDER))

    if hasattr(cmd_line_args, "print_env") and cmd_line_args.print_env:
        LOG.info("- Printing runtime environment")
        LOG.info(helpers.get_env_str(pkg_resources.working_set))

    LOG.info("- Getting app.configs")
    app_configs = helpers.get_configs(ALLOW_UNRECOGNIZED=True)

    check_pam_plugin_selftest(app_configs)
    check_soar_rest_connection(cmd_line_args, app_configs)
    check_soar_stomp_connection(cmd_line_args, app_configs)
    run_apps_selftest(cmd_line_args, app_configs)

    LOG.info("{0}selftest complete{0}".format(constants.LOG_DIVIDER))
