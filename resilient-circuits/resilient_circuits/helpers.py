#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common Helper Functions for resilient-circuits"""
import logging
import re

LOG = logging.getLogger("__name__")
FN_NAME_REGEX = re.compile(r'(?<=^\_)\w+(?=\_function$)')


def get_fn_name(names):
    """Returns the first string it finds in names of the function name
    if it matches _{FUNCTION-NAME}_function, else returns None.

    >>> get_fn_name(["don't return", "_fn_mock_integration_function"])
    'fn_mock_integration'

    >>> get_fn_name(["don't return", "_fn_mock_integration_functionX"])
    None

    >>> get_fn_name(["don't return", "X_fn_mock_integration_function"])
    None

    :param names: a list of strings to search
    :type names: list
    :return: fn_name: name of the function if found
    :rtype: str
    """
    assert isinstance(names, list)

    fn_name = None

    for n in names:
        if FN_NAME_REGEX.search(n):
            fn_name = FN_NAME_REGEX.findall(n)
            break

    if isinstance(fn_name, list) and len(fn_name) == 1:
        return fn_name[0]

    return fn_name


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
