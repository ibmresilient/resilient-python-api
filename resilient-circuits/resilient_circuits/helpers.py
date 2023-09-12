#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

"""Common Helper Functions for resilient-circuits"""
import copy
import logging
import re
import sys
import time

import pkg_resources
from resilient_circuits import constants
from six import string_types

from resilient import constants as res_constants
from resilient import (get_and_parse_proxy_env_var, get_client,
                       is_env_proxies_set)
from resilient.app_config import AppConfigManager

LOG = logging.getLogger("__name__")


def get_fn_names(component):
    """If `component` has a `function` attribute and it is True,
    appends the names in the function handler to `fn_names` and
    returns it, else returns an empty list.

    :param component: the component object to get it's list of function names for
    :type component: object
    :return: fn_names: the name in each function handler in the component if found
    :rtype: list
    """

    assert isinstance(component, object)

    fn_names = []

    # Get a list of callable methods for this object
    methods = [a for a in dir(component) if callable(getattr(component, a))]

    for m in methods:
        this_method = getattr(component, m)
        is_function = getattr(this_method, "function", False)

        if is_function:
            fn_decorator_names = this_method.names
            # Fail if fn_decorator_names is not a tuple as may have unhandled side effects if a str etc.
            # When a function handler is decorated its __init__() function takes the '*args' parameter
            # When * is prepended, it is known as an unpacking operator to allow the function handler to have
            # multiple names. args (or names in our case) will be a tuple, so if the logic of the function
            # decorator changes, this will catch it.
            assert isinstance(fn_decorator_names, tuple)
            for n in fn_decorator_names:
                fn_names.append(n)

    return fn_names


def get_handlers(component, handler_type="inbound_handler"):
    """If `component` has a `handler_type` attribute and it is True,
    appends a tuple to the handlers list and returns the list,
    else returns an empty list.

    Return example:
        -  `[(<method_name>, <method>, <handler_type>)]`
        -  `[('_inbound_app_mock_one', <function InboundAppComponent._inbound_app_mock_one at 0x10ccc9510>, 'inbound_handler')]`

    :param component: the component object to check if it's methods is a `handler_type`
    :type component: object
    :return: handlers: the name in each function handler in the component if found
    :rtype: list of tuples
    """

    assert isinstance(component, object)
    assert isinstance(handler_type, str)

    handlers = []

    # Get a list of callable methods for this object
    methods = [a for a in dir(component) if callable(getattr(component, a))]

    for m in methods:
        this_method = getattr(component, m)
        is_handler = getattr(this_method, handler_type, False)

        if is_handler:
            handlers.append((m, this_method, handler_type))

    return handlers


def check_exists(key, dict_to_check):
    """Returns the value of the key in dict_to_check if found,
    else returns False. If dict_to_check is None, returns False

    :param key: the key to look for in dict_to_check
    :type key: str
    :param dict_to_check: the key to look for in dict_to_check
    :type dict_to_check: dict
    :return: value of key in dict_to_check else False
    """
    if dict_to_check is None:
        return False

    assert isinstance(dict_to_check, dict)

    return dict_to_check.get(key, False)


def get_configs(path_config_file=None, ALLOW_UNRECOGNIZED=False):
    """
    Gets all the configs that are defined in the app.config file
    Uses the path to the config file from the parameter
    Or uses the `get_config_file()` method in resilient if None

    :param path_config_file: path to the app.config to parse
    :type path_config_file: str
    :param ALLOW_UNRECOGNIZED: bool to specify if AppArgumentParser will allow unknown comandline args or not. Default is False
    :type ALLOW_UNRECOGNIZED: bool
    :return: dictionary of all the configs in the app.config file
    :rtype: ``resilient.app_config.AppConfigManager``
    """
    from resilient_circuits.app_argument_parser import AppArgumentParser

    from resilient import get_config_file

    if not path_config_file:
        path_config_file = get_config_file()

    configs = AppArgumentParser(config_file=path_config_file).parse_args(ALLOW_UNRECOGNIZED=ALLOW_UNRECOGNIZED)
    return configs


def get_resilient_client(path_config_file=None, ALLOW_UNRECOGNIZED=False):
    """
    Return a SimpleClient for Resilient REST API using configurations
    options from provided path_config_file or from ~/.resilient/app.config

    :param path_config_file: path to the app.config to parse
    :type path_config_file: str
    :param ALLOW_UNRECOGNIZED: bool to specify if AppArgumentParser will allow unknown comandline args or not. Default is False
    :type ALLOW_UNRECOGNIZED: bool
    :return: SimpleClient for Resilient REST API
    :rtype: SimpleClient
    """
    client = get_client(get_configs(path_config_file=path_config_file, ALLOW_UNRECOGNIZED=ALLOW_UNRECOGNIZED))
    return client


def validate_configs(configs, validate_dict):
    """
    Checks if the configs are valid and raise a ValueError if they are not.
    Check if the config is required, has a value and meets its 'condition'

    :param configs: normally the configs in app.config
    :type configs: dict
    :param validate_dict: the key is the config and the value is a dict with the following params:
        - **required**: a boolean if the config is required
        - **placeholder_value**: the default value of the config that is not valid
        - **valid_condition**: a function to check if the value of the config is valid e.g. within a certain range
        - **invalid_msg**: displayed when valid_condition fails
    :type validate_dict: dict
    :return: nothing
    """
    if not isinstance(configs, dict):
        raise ValueError("'configs' must be of type dict, not {0}".format(type(configs)))

    if not isinstance(validate_dict, dict):
        raise ValueError("'validate_dict' must be of type dict, not {0}".format(type(validate_dict)))

    for config_name, config_validations in validate_dict.items():

        required = config_validations.get("required")
        placeholder_value = config_validations.get("placeholder_value")
        valid_condition = config_validations.get("valid_condition", lambda c: True)
        invalid_msg = config_validations.get("invalid_msg", "'{0}' did not pass it's validate condition".format(config_name))

        # get the config value from configs
        config = configs.get(config_name)

        # if its required
        if required:

            # if not in configs or empty string
            if not config:
                raise ValueError("'{0}' is mandatory and is not set in the config file.".format(config_name))

        # if still equals placeholder value
        if placeholder_value and config == placeholder_value:
            raise ValueError("'{0}' is mandatory and still has its placeholder value of '{1}' in the config file.".format(config_name, placeholder_value))

        # if meets its valid_condition
        if not valid_condition(config):
            raise ValueError(invalid_msg)


def get_packages(working_set):
    """
    Return a sorted list of tuples of all package names
    and their version in working_set

    :param working_set: the working_set for all packages installed in this env
    :type working_set: setuptools.pkg_resources.WorkingSet obj
    :return: pkg_list: a list of tuples [('name','version')] e.g. [('resilient-circuits', '39.0.0')].
        If ``working_set`` is not a ``pkg_resources.WorkingSet`` object, just return the current value of ``working_set``
    :rtype: list
    """

    if not isinstance(working_set, pkg_resources.WorkingSet):
        return working_set

    pkg_list = []

    for pkg in working_set:
        pkg_list.append((pkg.project_name, pkg.version))

    return sorted(pkg_list, key=lambda x: x[0].lower())


def get_env_str(packages):
    """
    Return a str with the Python version and the
    packages

    :param packages: the working_set for all packages installed in this env
    :type packages: setuptools.pkg_resources.WorkingSet obj
    :return: env_str: a str of the Environment
    :rtype: str
    """

    env_str = u"{0}Environment:\n".format(constants.LOG_DIVIDER)
    env_str += u"Python Version: {0}\n\n".format(sys.version)
    env_str += u"Installed packages:\n"
    for pkg in get_packages(packages):
        env_str += u"\n\t{0}: {1}".format(pkg[0], pkg[1])

    if is_env_proxies_set():

        proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTPS_PROXY)

        if not proxy_details:
            proxy_details = get_and_parse_proxy_env_var(res_constants.ENV_HTTP_PROXY)

        if proxy_details:
            env_str += u"\n\nConnecting through proxy: '{0}://{1}:{2}'".format(proxy_details.get("scheme"), proxy_details.get("hostname"), proxy_details.get("port"))

    env_str += u"\n###############"
    return env_str




def get_queue(destination):
    """
    Return a tuple (queue_type, org_id, queue_name).
    Returns None if fails to get queue

    :param destination: str in the format '/queue/actions.201.fn_main_mock_integration'
    :type destination: str
    :return: queue: (queue_type, org_id, queue_name) e.g. ('actions', '201', 'fn_main_mock_integration')
    :rtype: tuple
    """
    destination_str = destination

    try:
        assert isinstance(destination_str, str)

        # regex.sub to remove any /queue/ in the start
        regex = re.compile(r'\/.+\/')
        destination_str = re.sub(regex, "", destination_str, count=1)

        # split on periods to get the type, org_id, and queue name
        # use maxsplit=2 to only split on the first two periods,
        # as the third item might be a queue_name with a period in it
        # note in PY2 maxsplit is a positional arg so we don't label it here for compatiblity
        q = destination_str.split(".", 2)

        assert len(q) == 3

        return (tuple(q))

    except AssertionError as e:
        LOG.error("Could not get queue name from destination: '%s'\n%s", destination, str(e))
        return None


def is_this_a_selftest(component):
    """
    Return ``True`` or ``False`` if this instantiation of
    ``resilient-circuits`` is from selftest or not.

    :param component: the current component that is calling this method (usually ``self``)
    :type component: circuits.Component
    :rtype: bool
    """
    return component.IS_SELFTEST


def should_timeout(start_time, timeout_value):
    """
    Returns True if the delta between the
    start_time and the current_time is greater

    All time values are the time in seconds since
    the epoch as a floating point number

    :param start_time: the time before the loop starts
    :type start_time: float
    :param timeout_value: number of seconds to timeout after
    :type timeout_value: int/float
    :rtype: bool
    """
    return (time.time() - start_time) > timeout_value


def get_user(app_configs):
    """
    Looks for either 'api_key_id' or 'email'
    in the provided dict and returns its value.

    Returns None if neither are found or set to
    a valid value

    :param app_configs: a dictionary of all the values in the app.config file
    :type app_configs: dict
    :rtype: [str/None]
    """
    usr = app_configs.get("api_key_id", None)

    if not usr:
        usr = app_configs.get("email", None)

        if not usr:
            return None

    return usr


def filter_heartbeat_timeout_events(heartbeat_timeouts):
    """
    Sort a list of HeartbeatTimeout on their ts and
    remove an occurrences of HeartbeatTimeout whose ts
    value is -1

    :param heartbeat_timeouts: List of HeartbeatTimeout
    :type heartbeat_timeouts: [HeartbeatTimeout]
    :return: Sorted and filtered list of HeartbeatTimeout
    :rtype: [HeartbeatTimeout]
    """

    if not heartbeat_timeouts:
        return heartbeat_timeouts

    # Remove any elements whose ts is -1
    heartbeat_timeouts = [hb for hb in heartbeat_timeouts if hb.ts != -1]

    heartbeat_timeouts.sort()

    return heartbeat_timeouts

def sub_fn_inputs_from_protected_secrets(fn_inputs, opts):
    """
    Substitute any protected secret *or regular secret
    into a function input. Requires the ``opts`` dictionary
    (usually actually a AppConfigManager object) to be 
    given to properly create a temporary AppConfigManager
    that will have access to the pam plugin if relevant.

    This supports the same syntax as secrets in app.config:
      - if $ or ^ starts a string, if the following string
        is found in secrets, it will be replaced
      - if ${} or ^{} is found within a string, the value
        there will be replaced with the appropriate secret
        if found
    In either case, if the value following the reserved character
    is not found in secrets, the original value will remain and no
    substitution will be made.

    **Example:**

    .. code-block::python

        fn_inputs = {"fn_my_app_input_1": "Sub in ${HERE}"}
        fn_inputs = helpers.sub_fn_inputs_from_protected_secrets(fn_inputs, opts)
        assert fn_inputs["fn_my_app_input_1"] == "Sub in <value from secrets>"

    :param fn_inputs: function inputs as a dictionary (retrieved from the event message)
    :type fn_inputs: dict
    :param opts: app configs from AppFunctionComponent (usually self.opts)
    :type opts: AppConfigManager | dict
    :return: fn_inputs unchanged except where secrets referenced are replaced
    :rtype: dict
    """
    fn_inputs = copy.deepcopy(fn_inputs)

    # find the pam_plugin type if necessary
    if isinstance(opts, AppConfigManager) and opts.pam_plugin:
        pam_plugin = type(opts.pam_plugin)
    else:
        pam_plugin = None

    # use a AppConfigManager temporarily to take advantage of its
    # protected secrets and PAM secrets substitution capabilities
    fn_inputs_manager = AppConfigManager(fn_inputs, pam_plugin)

    # since the value for fn_inputs will quickly be translated
    # to a namedtuple anyway, we simply set the values to the
    # substituted values from the AppConfigManager here.
    # This is different from how we'd use the AppConfigManager
    # within the rest of the function code, where we'd usually
    # persist the object so that values (especially PAM values)
    # are guaranteed to be up to date. in this case, these values
    # will be used relatively quickly within a function so we can
    # statically save the found value here and we assume it will
    # be used quickly enough in the function to be up to date.
    # NOTE: some inputs might not be strings. in that case,
    # they will not be substituted, they will remain their
    # original value and structure. This applies to ints,
    # multiselects, booleans, and date time pickers.
    # All text, text with string, and select (single) inputs
    # will attempt to substitute if applicable
    for key in fn_inputs_manager:
        if isinstance(fn_inputs[key], string_types):
            fn_inputs[key] = fn_inputs_manager[key]

    return fn_inputs
