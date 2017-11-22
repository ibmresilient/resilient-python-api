# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
import pytest
import unittest
import mock
from resilient.bin.res_keyring import KeyringUtils

class TestKeyringUtils(unittest.TestCase):
    mocked_resilient_class = mock.Mock()
    mocked_resilient_get_config = mock.Mock()
    @mock.patch("resilient.get_config_file", mocked_resilient_get_config)
    def test_run(self):
        mocked_get_config = mock.Mock()
        mocked_get_config = self.mocked_resilient_class.get_config_file.return_value

        keyring_util = KeyringUtils()
        keyring_util.run()

        assert keyring_util



