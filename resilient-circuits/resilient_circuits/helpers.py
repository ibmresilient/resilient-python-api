#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common Helper Functions for resilient-circuits"""
import sys
import pkg_resources
import logging
import copy
import re

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
    :return: pkg_list: a list of tuples [('name','version')] e.g. [('resilient-circuits', '39.0.0')]
    :rtype: list
    """

    isinstance(working_set, pkg_resources.WorkingSet)

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

    env_str = u"###############\n\nEnvironment:\n\n"
    env_str += u"Python Version: {0}\n\n".format(sys.version)
    env_str += u"Installed packages:\n"
    for pkg in get_packages(packages):
        env_str += u"\n\t{0}: {1}".format(pkg[0], pkg[1])
    env_str += u"\n###############"
    return env_str


def remove_tag(original_res_obj):
    """
    Return the original_res_obj with any of the "tags"
    attribute set to an empty list

    Example:
    ```
    mock_res_obj = {
        "tags": [{"tag_handle": "fn_tag_test", "value": None}],
        "functions": [
            {"export_key": "fn_tag_test_function",
            "tags": [{'tag_handle': 'fn_tag_test', 'value': None}]}
        ]
    }

    new_res_obj = remove_tag(mock_res_obj)

    Returns: {
        "tags": [],
        "functions": [
            {"export_key": "fn_tag_test_function", "tags": []}
        ]
    }
    ```
    :param original_res_obj: the res_obj you want to remove the tags attribute from
    :type original_res_obj: dict
    :return: new_res_obj: a dict with the tag attribute removed
    :rtype: dict
    """
    ATTRIBUTE_NAME = "tags"

    new_res_obj = copy.deepcopy(original_res_obj)

    if isinstance(new_res_obj, dict):

        # Set "tags" to empty list
        if new_res_obj.get(ATTRIBUTE_NAME):
            new_res_obj[ATTRIBUTE_NAME] = []

        # Recursively loop the dict
        for obj_name, obj_value in new_res_obj.items():

            if isinstance(obj_value, list):
                for index, obj in enumerate(obj_value):
                    new_res_obj[obj_name][index] = remove_tag(obj)

            elif isinstance(obj_value, dict):
                new_res_obj[obj_name] = remove_tag(obj_value)

    return new_res_obj
