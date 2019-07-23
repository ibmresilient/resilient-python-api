import unittest
import os
import sys
import shutil
import copy
import zipfile
import json
from resilient_circuits.util.ext.ExtCreate import ExtCreate, PATH_DEFAULT_ICON_EXTENSION_LOGO, PATH_DEFAULT_ICON_COMPANY_LOGO
from resilient_circuits.util.ext import ExtException

# Import mock_data (need to add path to support relative imports in PY3)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ext_tests.mock_data.mock_data import MOCK_INTEGRATION_NAME, MOCK_INTEGRATION_URL, MOCK_INTEGRATION_LONG_DESCRIPTION, mock_import_definition, mock_import_definition_tagged, mock_config_str, mock_config_list, mock_setup_py_file_lines, mock_parsed_setup_py_attributes, mock_icon_extension_logo, mock_icon_company_logo, mock_message_destination_to_be_tagged, mock_message_destination_tagged, mock_extension_zip_file_structure, mock_executables_zip_file_structure

path_this_dir = os.path.dirname(os.path.realpath(__file__))
path_temp_test_dir = os.path.join(path_this_dir, "test_temp")
path_fn_mock_integration = os.path.join(path_this_dir, "mock_data", "fn_mock_integration")
path_mock_setup_py_file = os.path.join(path_fn_mock_integration, "setup.py")
path_mock_customize_py_file = os.path.join(path_fn_mock_integration, "fn_mock_integration", "util", "customize.py")
path_mock_config_py_file = os.path.join(path_fn_mock_integration, "fn_mock_integration", "util", "config.py")
path_mock_bd_true_tar = os.path.join(path_this_dir, "mock_data", "built_distributions", "true_tar_fn_mock_integration-1.0.0.tar.gz")
path_mock_bd_true_zip = os.path.join(path_this_dir, "mock_data", "built_distributions", "true_zip_fn_mock_integration-1.0.0.zip")
path_mock_bd_zipped_tar = os.path.join(path_this_dir, "mock_data", "built_distributions", "zipped_tar_fn_mock_integration-1.0.0.zip")

path_mock_export_res = os.path.join(path_this_dir, "mock_data", "ext-fn_mock_integration-1.0.0", "export.res")
path_mock_extension_json = os.path.join(path_this_dir, "mock_data", "ext-fn_mock_integration-1.0.0", "extension.json")
path_mock_exectuable_json = os.path.join(path_this_dir, "mock_data", "ext-fn_mock_integration-1.0.0", "executables", "executable.json")


def get_dict_from_json_file(file_path):
    dict_to_return = {}
    with open(file_path, 'r') as the_file:
            dict_to_return = json.load(the_file)
    return dict_to_return


class ExtCreateClassTestIndividualFns(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        # assertRaisesRegexp renamed to assertRaisesRegex in PY3.2
        if sys.version_info < (3, 2):
            self.assertRaisesRegex = self.assertRaisesRegexp

        self.ext_create_class = ExtCreate("ext:package")
        self.original_import_definition = copy.deepcopy(mock_import_definition)
        self.original_mock_message_destination_to_be_tagged = copy.deepcopy(mock_message_destination_to_be_tagged[0])

    def tearDown(self):
        # Reset mock_import_definition object
        mock_import_definition.clear()
        mock_import_definition.update(copy.deepcopy(self.original_import_definition))

        # Reset mock_message_destination_to_be_tagged
        mock_message_destination_to_be_tagged[0].clear()
        mock_message_destination_to_be_tagged[0].update(copy.deepcopy(self.original_mock_message_destination_to_be_tagged))

    def test_get_import_definition_from_customize_py(self):
        import_definition = self.ext_create_class.__get_import_definition_from_customize_py__(path_mock_customize_py_file)

        self.assertEqual(import_definition, mock_import_definition)

    def test_get_configs_from_config_py(self):
        the_config_str, the_config_list = self.ext_create_class.__get_configs_from_config_py__(path_mock_config_py_file)

        self.assertEqual(the_config_str, mock_config_str)
        self.assertEqual(the_config_list, mock_config_list)

    def test_parse_setup_attribute(self):
        the_parsed_name_value = self.ext_create_class.__parse_setup_attribute__(path_mock_setup_py_file, mock_setup_py_file_lines, "name")
        self.assertEqual(the_parsed_name_value, MOCK_INTEGRATION_NAME)

        the_parsed_url_value = self.ext_create_class.__parse_setup_attribute__(path_mock_setup_py_file, mock_setup_py_file_lines, "url")
        self.assertEqual(the_parsed_url_value, MOCK_INTEGRATION_URL)

        the_parsed_long_description_value = self.ext_create_class.__parse_setup_attribute__(path_mock_setup_py_file, mock_setup_py_file_lines, "long_description")
        self.assertEqual(the_parsed_long_description_value, MOCK_INTEGRATION_LONG_DESCRIPTION)

    def test_parse_setup_py(self):
        attribute_names = self.ext_create_class.supported_setup_py_attribute_names
        parsed_setup_py_attributes = self.ext_create_class.__parse_setup_py__(path_mock_setup_py_file, attribute_names)
        self.assertEqual(parsed_setup_py_attributes, mock_parsed_setup_py_attributes)

    def test_get_icon(self):

        path_extension_logo = os.path.join(path_fn_mock_integration, "icons", "extension_logo.png")
        path_company_logo = os.path.join(path_fn_mock_integration, "icons", "company_logo.png")

        path_to_corrupt_jpg_icon = os.path.join(path_fn_mock_integration, "icons", "mock_corrupt_icon.jpg")
        path_to_corrupt_png_icon = os.path.join(path_fn_mock_integration, "icons", "mock_corrupt_icon.png")

        # Test getting extension_logo
        extension_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_extension_logo, 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

        # Test getting default extension_logo
        extension_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), "", 200, 72, PATH_DEFAULT_ICON_EXTENSION_LOGO)
        self.assertEqual(extension_logo_as_base64, mock_icon_extension_logo)

        # Test getting company_logo
        company_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), path_company_logo, 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
        self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

        # Test getting default company_logo
        company_logo_as_base64 = self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), "", 100, 100, PATH_DEFAULT_ICON_COMPANY_LOGO)
        self.assertEqual(company_logo_as_base64, mock_icon_company_logo)

        # Test invalid paths
        with self.assertRaisesRegex(OSError, "Could not find valid icon file. Looked at two locations:"):
            self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_COMPANY_LOGO), "", 200, 72, "")

        # Test not .png
        with self.assertRaisesRegex(ExtException, ".jpg is not a supported icon file type. Icon file must be .png"):
            self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_to_corrupt_jpg_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)

        # Test corrupt .png
        with self.assertRaisesRegex(ExtException, "Icon file corrupt"):
            self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_to_corrupt_png_icon, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)

        # Test invalid resolution
        with self.assertRaisesRegex(ExtException, "Resolution must be 10x10"):
            self.ext_create_class.__get_icon__(os.path.basename(PATH_DEFAULT_ICON_EXTENSION_LOGO), path_extension_logo, 10, 10, PATH_DEFAULT_ICON_EXTENSION_LOGO)

    def test_add_tag(self):
        tag_name = MOCK_INTEGRATION_NAME

        # Test adding the tag
        tagged_md = self.ext_create_class.__add_tag__(tag_name, mock_message_destination_to_be_tagged)
        self.assertEqual(tagged_md, mock_message_destination_tagged)

        # Test invalid list_of_objs
        with self.assertRaisesRegex(ExtException, "is not a List"):
            self.ext_create_class.__add_tag__(tag_name, "")

    def test_add_tag_to_import_definition(self):
        tag_name = MOCK_INTEGRATION_NAME
        supported_res_obj_names = self.ext_create_class.supported_res_obj_names
        tagged_import_definition = self.ext_create_class.__add_tag_to_import_definition__(tag_name, supported_res_obj_names, mock_import_definition)

        self.assertEqual(tagged_import_definition, mock_import_definition_tagged)


class ExtCreateClassTestCreateExtension(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        self.ext_create_class = ExtCreate("ext:package")

        # Create temp dir
        os.makedirs(path_temp_test_dir)

    def tearDown(self):
        # Remove temp dir
        shutil.rmtree(path_temp_test_dir)

    def create_the_extension(self, path_built_distribution):
        return self.ext_create_class.create_extension(
            path_setup_py_file=path_mock_setup_py_file,
            path_customize_py_file=path_mock_customize_py_file,
            path_config_py_file=path_mock_config_py_file,
            output_dir=path_temp_test_dir,
            path_built_distribution=path_built_distribution
        )

    def validate_creation(self, path_the_extension_zip):
        path_created_extension_zip = os.path.join(path_temp_test_dir, "ext-fn_mock_integration-1.0.0.zip")

        self.assertEqual(path_the_extension_zip, path_created_extension_zip)
        self.assertTrue(zipfile.is_zipfile(path_the_extension_zip))

    def validate_extension_zip_folder_structure(self, path_the_extension_zip):
        # Open the zip
        with zipfile.ZipFile(file=path_the_extension_zip, mode="r") as zip_file:
            # Get a List of all the member names
            zip_file_structure = zip_file.namelist()

        self.assertEqual(zip_file_structure, mock_extension_zip_file_structure)

    def validate_executables_folder_structure(self, path_the_extension_zip):
        # Open the extension_zip
        with zipfile.ZipFile(file=path_the_extension_zip, mode="r") as the_extension_zip_file:
            # Extract the executables_zip
            path_the_executable_zip_file = the_extension_zip_file.extract(member="executables/exe-{0}-1.0.0.zip".format(MOCK_INTEGRATION_NAME), path=path_temp_test_dir)

        # Open the executables_zip
        with zipfile.ZipFile(file=path_the_executable_zip_file, mode="r") as the_executable_zip_file:
            the_executable_zip_file_structure = the_executable_zip_file.namelist()

        self.assertEqual(the_executable_zip_file_structure, mock_executables_zip_file_structure)

    def validate_export_res_and_extension_json(self, path_the_extension_zip):
        # Get the mock data
        mock_export_res = get_dict_from_json_file(path_mock_export_res)
        mock_extension_json = get_dict_from_json_file(path_mock_extension_json)

        # Extract the zip
        with zipfile.ZipFile(file=path_the_extension_zip, mode="r") as zip_file:
            zip_file.extractall(path=path_temp_test_dir)

        # Get the export_res and extension_json
        export_res = get_dict_from_json_file(os.path.join(path_temp_test_dir, "export.res"))
        extension_json = get_dict_from_json_file(os.path.join(path_temp_test_dir, "extension.json"))

        # Compare
        self.assertEqual(export_res, mock_export_res)
        self.assertEqual(mock_extension_json, extension_json)

    def validate_executable_json(self, path_the_extension_zip):
        # Get the mock data
        mock_executable_json = get_dict_from_json_file(path_mock_exectuable_json)

        # Open the extension_zip
        with zipfile.ZipFile(file=path_the_extension_zip, mode="r") as the_extension_zip_file:
            # Extract the executables_zip
            path_the_executable_zip_file = the_extension_zip_file.extract(member="executables/exe-{0}-1.0.0.zip".format(MOCK_INTEGRATION_NAME), path=path_temp_test_dir)

        # Open the executables_zip
        with zipfile.ZipFile(file=path_the_executable_zip_file, mode="r") as the_executable_zip_file:
            the_executable_zip_file.extractall(path=path_temp_test_dir)

        # Get the executable.json
        executable_json = get_dict_from_json_file(os.path.join(path_temp_test_dir, "executable.json"))

        # Compare
        self.assertEqual(executable_json, mock_executable_json)

    #################
    # Test TRUE TAR #
    #################
    def test_true_tar_creation(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_tar)

        # Validate creation
        self.validate_creation(path_the_extension_zip)

    def test_true_tar_valid_extension_zip_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_tar)

        # Validate folder structure
        self.validate_extension_zip_folder_structure(path_the_extension_zip)

    def test_true_tar_valid_executables_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_tar)

        # Validate folder structure
        self.validate_executables_folder_structure(path_the_extension_zip)

    def test_true_tar_valid_export_res_and_extension_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_tar)

        # Validate export.res and extension.json
        self.validate_export_res_and_extension_json(path_the_extension_zip)

    def test_true_tar_valid_executables_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_tar)

        # Validate export.res and extension.json
        self.validate_executable_json(path_the_extension_zip)

    #################
    # Test TRUE ZIP #
    #################
    def test_true_zip_creation(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_zip)

        # Validate creation
        self.validate_creation(path_the_extension_zip)

    def test_true_zip_valid_extension_zip_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_zip)

        # Validate folder structure
        self.validate_extension_zip_folder_structure(path_the_extension_zip)

    def test_true_zip_valid_executables_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_zip)

        # Validate folder structure
        self.validate_executables_folder_structure(path_the_extension_zip)

    def test_true_zip_valid_export_res_and_extension_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_zip)

        # Validate export.res and extension.json
        self.validate_export_res_and_extension_json(path_the_extension_zip)

    def test_true_zip_valid_executables_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_true_zip)

        # Validate export.res and extension.json
        self.validate_executable_json(path_the_extension_zip)

    ###################
    # Test ZIPPED TAR #
    ###################
    def test_zipped_tar_creation(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_zipped_tar)

        # Validate creation
        self.validate_creation(path_the_extension_zip)

    def test_zipped_tar_valid_extension_zip_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_zipped_tar)

        # Validate folder structure
        self.validate_extension_zip_folder_structure(path_the_extension_zip)

    def test_zipped_tar_valid_executables_folder_structure(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_zipped_tar)

        # Validate folder structure
        self.validate_executables_folder_structure(path_the_extension_zip)

    def test_zipped_tar_valid_export_res_and_extension_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_zipped_tar)

        # Validate export.res and extension.json
        self.validate_export_res_and_extension_json(path_the_extension_zip)

    def test_zipped_tar_valid_executables_json(self):
        # Create the extension
        path_the_extension_zip = self.create_the_extension(path_mock_bd_zipped_tar)

        # Validate export.res and extension.json
        self.validate_executable_json(path_the_extension_zip)