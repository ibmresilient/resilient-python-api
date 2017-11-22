# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
import pytest
import unittest
import mock
from resilient.bin.finfo import FinfoArgumentParser, print_details, find_field, list_fields_values, list_fields_csv,list_fields, list_types



class TestFinfoArgumentParser(unittest.TestCase):
    def test_print_details(self):
        print_details({"id": "1", "name": "test", "text": "test", "value": "1234", "input_type": "test",
                       "prefix": "test", "tooltip": "test", "placeholder": "test"})

    def test_find_field(self):
        mocked_rest_client = mock.Mock()
        mocked_get_call = mock.Mock()
        mocked_rest_client.get = mocked_get_call.return_value
        mocked_rest_client.get.side_effect = client_return
        mocked_get_call.__len__ = lambda s: 100

        field = find_field(mocked_rest_client, "test")
        assert field


    def test_list_fields_values(self):
        mocked_rest_client = mock.Mock()
        mocked_get_call = mock.Mock()
        mocked_rest_client.get = mocked_get_call.return_value
        mocked_rest_client.get.side_effect = client_return
        mocked_get_call.__len__ = lambda s: 100

        list_fields_values(mocked_rest_client)

    def test_list_fields_csv(self):
        mocked_rest_client = mock.Mock()
        mocked_get_call = mock.Mock()
        mocked_rest_client.get = mocked_get_call.return_value
        mocked_rest_client.get.side_effect = client_return
        mocked_get_call.__len__ = lambda s: 100

        list_fields_csv(mocked_rest_client)

    def test_list_fields(self):
        mocked_rest_client = mock.Mock()
        mocked_get_call = mock.Mock()
        mocked_rest_client.get = mocked_get_call.return_value
        mocked_rest_client.get.side_effect = client_return
        mocked_get_call.__len__ = lambda s: 100

        list_fields(mocked_rest_client)


def client_return(*args, **kwargs):
    inStr = str(args[0])
    ret = []
    if inStr == "/types":
        ret = [{"test": {"id": "1", "name": "test", "text": "test", "value": "1234", "input_type": "test",
                "prefix": "test", "tooltip": "test", "placeholder": "test"}}]
    elif inStr == "/types/incident/fields":
        ret = [{"id": "1", "name": "test", "text": "test", "value": "1234", "input_type": "test",
                "prefix": "test", "tooltip": "test", "placeholder": "test"}]
    return ret