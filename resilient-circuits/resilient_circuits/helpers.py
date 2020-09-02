#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""Common Helper Functions for resilient-circuits"""
import logging
import re

LOG = logging.getLogger("__name__")


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
    :type names: List
    :return: fn_name: name of the function if found
    :rtype: Str
    """
    assert isinstance(names, list)

    regex = re.compile(r'(?<=^\_)\w+(?=\_function$)')
    fn_name = None

    for n in names:
        if regex.search(n):
            fn_name = regex.findall(n)
            break

    if isinstance(fn_name, list) and len(fn_name) == 1:
        return fn_name[0]

    return fn_name
