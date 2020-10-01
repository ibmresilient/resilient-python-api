import unittest
from resilient_circuits.util.resilient_ext import ext_command_handler
from resilient_circuits.util.ext import ExtException


class TestExtCmdHandler(unittest.TestCase):

    def test_unsupported_cmd(self):

        with self.assertRaises(ExtException) as cm:
            ext_command_handler("mock_cmd", {"path_to_package": "/mock/path"})

        the_exception = cm.exception
        self.assertIn("Unsupported command", the_exception.message)
