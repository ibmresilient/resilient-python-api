# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
import pytest
import unittest
import mock
from resilient.co3sslutil import match_hostname


class TestCo3SSLUtil(unittest.TestCase):
    def test_match_hostname(self):
        with pytest.raises(Exception):
            match_hostname(mock.Mock(), "test.com")
