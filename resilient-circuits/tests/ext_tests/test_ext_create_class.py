import unittest
import os
import shutil
import copy
import logging
from resilient_circuits.util.ext.ExtCreate import ExtCreate, PATH_DEFAULT_ICON_EXTENSION_LOGO, PATH_DEFAULT_ICON_COMPANY_LOGO
from resilient_circuits.util.ext import ExtException
from mock_data.mock_data import MOCK_INTEGRATION_NAME, MOCK_INTEGRATION_URL, MOCK_INTEGRATION_LONG_DESCRIPTION, mock_import_definition, mock_import_definition_tagged, mock_config_str, mock_config_list, mock_setup_py_file_lines, mock_parsed_setup_py_attributes, mock_icon_extension_logo, mock_icon_company_logo, mock_message_destination_to_be_tagged, mock_message_destination_tagged

LOG = logging.getLogger("testing_logger")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())

class TestExtClass(unittest.TestCase):

    maxDiff = None
    path_this_dir = os.path.dirname(os.path.realpath(__file__))
    path_fn_mock_integration = os.path.join(path_this_dir, "mock_data", "fn_mock_integration")
    path_mock_setup_py_file = os.path.join(path_fn_mock_integration, "setup.py")
    path_mock_customize_py_file = os.path.join(path_fn_mock_integration, "fn_mock_integration", "util", "customize.py")
    path_mock_config_py_file = os.path.join(path_fn_mock_integration, "fn_mock_integration", "util", "config.py")

    def assertException(self, the_exception, message):
        self.assertIn(message, the_exception.message)

    def setUp(self):
        self.ext_create_class = ExtCreate("ext:package")
        self.original_import_definition = copy.deepcopy(mock_import_definition)

    def tearDown(self):
        mock_import_definition.clear()
        mock_import_definition.update(copy.deepcopy(self.original_import_definition))

    def test_get_import_definition_from_customize_py(self):
        import_definition = self.ext_create_class.__get_import_definition_from_customize_py__(self.path_mock_customize_py_file)

        self.assertEqual(import_definition, mock_import_definition)

    def test_get_configs_from_config_py(self):
        the_config_str, the_config_list = self.ext_create_class.__get_configs_from_config_py__(self.path_mock_config_py_file)

        self.assertEqual(the_config_str, mock_config_str)
        self.assertEqual(the_config_list, mock_config_list)

    def test_parse_setup_attribute(self):
        the_parsed_name_value = self.ext_create_class.__parse_setup_attribute__(self.path_mock_setup_py_file, mock_setup_py_file_lines, "name")
        self.assertEqual(the_parsed_name_value, MOCK_INTEGRATION_NAME)

        the_parsed_url_value = self.ext_create_class.__parse_setup_attribute__(self.path_mock_setup_py_file, mock_setup_py_file_lines, "url")
        self.assertEqual(the_parsed_url_value, MOCK_INTEGRATION_URL)

        the_parsed_long_description_value = self.ext_create_class.__parse_setup_attribute__(self.path_mock_setup_py_file, mock_setup_py_file_lines, "long_description")
        self.assertEqual(the_parsed_long_description_value, MOCK_INTEGRATION_LONG_DESCRIPTION)

    def test_parse_setup_py(self):
        attribute_names = self.ext_create_class.supported_setup_py_attribute_names
        parsed_setup_py_attributes = self.ext_create_class.__parse_setup_py__(self.path_mock_setup_py_file, attribute_names)
        self.assertEqual(parsed_setup_py_attributes, mock_parsed_setup_py_attributes)

    def test_get_icon(self):

        path_extension_logo = os.path.join(self.path_fn_mock_integration, "icons", "extension_logo.png")
        path_company_logo = os.path.join(self.path_fn_mock_integration, "icons", "company_logo.png")
        
        path_to_corrupt_jpg_icon = os.path.join(self.path_fn_mock_integration, "icons", "mock_corrupt_icon.jpg")
        path_to_corrupt_png_icon = os.path.join(self.path_fn_mock_integration, "icons", "mock_corrupt_icon.png")

        # Test getting extension_logo
        extension_logo_as_base64 = self.ext_create_class.__get_icon__(path_extension_logo, 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

        # Test getting default extension_logo
        extension_logo_as_base64 = self.ext_create_class.__get_icon__("", 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

        # Test getting company_logo
        company_logo_as_base64 = self.ext_create_class.__get_icon__(path_company_logo, 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
        self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

        # Test getting default company_logo
        company_logo_as_base64 = self.ext_create_class.__get_icon__("", 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
        self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

        # Test invalid paths
        with self.assertRaises(OSError) as cm:
            self.ext_create_class.__get_icon__("", 200, 72, "")
        self.assertException(cm.exception, "Could not find valid icon file. Looked at two locations:")

        # Test not .png
        with self.assertRaises(ExtException) as cm:
            self.ext_create_class.__get_icon__(path_to_corrupt_jpg_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertException(cm.exception, ".jpg is not a supported icon file type. Icon file must be .png")

        # Test corrupt .png
        with self.assertRaises(ExtException) as cm:
            self.ext_create_class.__get_icon__(path_to_corrupt_png_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertException(cm.exception, "Icon file corrupt")

        # Test invalid resolution
        with self.assertRaises(ExtException) as cm:
            self.ext_create_class.__get_icon__(path_extension_logo, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertException(cm.exception, "Resolution must be 10x10")

    def test_add_tag(self):
        tag_name = MOCK_INTEGRATION_NAME
        
        # Test adding the tag
        tagged_md = self.ext_create_class.__add_tag__(tag_name, mock_message_destination_to_be_tagged)
        self.assertEqual(tagged_md, mock_message_destination_tagged)
        
         # Test invalid list_of_objs
        with self.assertRaises(ExtException) as cm:
            self.ext_create_class.__add_tag__(tag_name, "")
        self.assertException(cm.exception, "is not a List")

    def test_add_tag_to_import_definition(self):
        tag_name = MOCK_INTEGRATION_NAME
        supported_res_obj_names = self.ext_create_class.supported_res_obj_names
        tagged_import_definition = self.ext_create_class.__add_tag_to_import_definition__(tag_name, supported_res_obj_names, mock_import_definition)

        self.assertEqual(tagged_import_definition, mock_import_definition_tagged)

