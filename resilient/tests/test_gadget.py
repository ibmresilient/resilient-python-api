# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
import pytest
import unittest
import mock
from resilient.bin.gadget import ExampleArgumentParser, \
    generic_get, generic_post, generic_update, generic_patch, generic_search


class TestExampleArgumentParser(unittest.TestCase):
    def test_run(self):

        exampleAP = ExampleArgumentParser(config_file=None)

        assert exampleAP

    def test_generic_get(self):
        mocked_rest_client = mock.Mock()
        mocked_get_call = mock.Mock()
        mocked_rest_client.get = mocked_get_call.return_value
        mocked_rest_client.get.side_effect = client_return
        mocked_get_call.__len__ = lambda s: 100

        generic_get(mocked_rest_client, "test")

    def test_generic_post(self):
        mocked_rest_client = mock.Mock()
        mocked_post_call = mock.Mock()
        mocked_rest_client.post = mocked_post_call.return_value
        mocked_rest_client.post.side_effect = client_return
        mocked_post_call.__len__ = lambda s: 100

        generic_post(mocked_rest_client, "test", "template_test.json")

    def test_generic_update(self):
        mocked_rest_client = mock.Mock()
        mocked_get_put_call = mock.Mock()
        mocked_rest_client.get_put = mocked_get_put_call.return_value
        mocked_rest_client.get_put.side_effect = client_return
        mocked_get_put_call.__len__ = lambda s: 100

        generic_update(mocked_rest_client, "test", "template_test.json")

    def test_generic_patch(self):
        mocked_rest_client = mock.Mock()
        mocked_patch_call = mock.Mock()
        mocked_rest_client.patch = mocked_patch_call.return_value
        mocked_rest_client.patch.side_effect = client_return
        mocked_patch_call.__len__ = lambda s: 100

        generic_patch(mocked_rest_client, "test", "template_test.json")

    def test_generic_search(self):
        mocked_rest_client = mock.Mock()
        mocked_search_call = mock.Mock()
        mocked_rest_client.search = mocked_search_call.return_value
        mocked_rest_client.search.side_effect = client_return
        mocked_search_call.__len__ = lambda s: 100

        generic_search(mocked_rest_client, "template_test.json")

def client_return(*args, **kwargs):
    return {"id": "id"}