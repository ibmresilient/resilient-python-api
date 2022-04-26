#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import os
import io
import json
from tests.shared_mock_data import mock_paths


def read_json_file(path):
    """
    If the contents of the file at path is valid JSON,
    returns the contents of the file as a dictionary

    :param path: Path to JSON file to read
    :type path: str
    :return: File contents as a dictionary
    :rtype: dict
    """
    file_contents = None
    with io.open(path, mode="rt", encoding="utf-8") as the_file:
        try:
            file_contents = json.load(the_file)
        # In PY2.7 it raises a ValueError and in PY3.6 it raises
        # a JSONDecodeError if it cannot load the JSON from the file
        except (ValueError, JSONDecodeError) as err:
            raise Exception("Could not read corrupt JSON file at {0}\n{1}".format(path, err))
    return file_contents


def get_mock_response(response_name):
    """
    Reads the JSON file at shared_mock_data/<response>.JSON
    and returns it as a dict

    :param response_name: name of response file - e.g if session.JSON wanted the param is 'session'
    :type response_name: str
    :return: File contents as a dictionary
    :rtype: dict
    """
    path_mock_response = os.path.join(mock_paths.MOCK_RESPONSES_DIR, "{0}.JSON".format(response_name))

    if not os.path.isfile(path_mock_response):
        raise Exception("{0} is not a valid file".format(path_mock_response))

    return read_json_file(path_mock_response)
