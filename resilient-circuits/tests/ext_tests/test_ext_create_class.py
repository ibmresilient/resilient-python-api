import unittest
import os
import shutil
import logging
from resilient_circuits.util.ext.ExtCreate import ExtCreate
from resilient_circuits.util.ext import ExtException
from mock_data.mock_data import MOCK_INTEGRATION_NAME, MOCK_INTEGRATION_URL, MOCK_INTEGRATION_LONG_DESCRIPTION, mock_import_definition, mock_config_str, mock_config_list, mock_setup_py_file_lines

LOG = logging.getLogger("testing_logger")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

class TestExtClass(unittest.TestCase):

    def assertException(self, the_exception, message):
        self.assertIn(message, the_exception.message)

    def setUp(self):
        self.ext_create_class = ExtCreate("ext:package")
        self.path_this_dir = os.path.dirname(os.path.realpath(__file__))
        self.path_fn_mock_integration = os.path.join(self.path_this_dir, "mock_data", "fn_mock_integration")
        # self.temp_dir = os.path.join(self.path_this_dir, "test_temp")
        # os.makedirs(self.temp_dir)

    def tearDown(self):
        # shutil.rmtree(self.temp_dir)
        pass

    def test_get_import_definition_from_customize_py(self):
        path_customize_py_file = os.path.join(self.path_fn_mock_integration, "fn_mock_integration", "util", "customize.py")

        import_definition = self.ext_create_class.__get_import_definition_from_customize_py__(path_customize_py_file)

        self.assertEquals(import_definition, mock_import_definition)

    def test_get_configs_from_config_py(self):
        path_config_py_file = os.path.join(self.path_fn_mock_integration, "fn_mock_integration", "util", "config.py")

        the_config_str, the_config_list = self.ext_create_class.__get_configs_from_config_py__(path_config_py_file)

        self.assertEquals(the_config_str, mock_config_str)
        self.assertEquals(the_config_list, mock_config_list)

    def test_parse_setup_attribute(self):
        path_setup_py_file = os.path.join(self.path_fn_mock_integration, "setup.py")

        the_parsed_name_value = self.ext_create_class.__parse_setup_attribute__(path_setup_py_file, mock_setup_py_file_lines, "name")
        self.assertEquals(the_parsed_name_value, MOCK_INTEGRATION_NAME)

        the_parsed_url_value = self.ext_create_class.__parse_setup_attribute__(path_setup_py_file, mock_setup_py_file_lines, "url")
        self.assertEquals(the_parsed_url_value, MOCK_INTEGRATION_URL)

        the_parsed_long_description_value = self.ext_create_class.__parse_setup_attribute__(path_setup_py_file, mock_setup_py_file_lines, "long_description")
        self.assertEquals(the_parsed_long_description_value, MOCK_INTEGRATION_LONG_DESCRIPTION)
