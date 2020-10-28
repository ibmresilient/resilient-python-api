import unittest
import os
import sys
import shutil
import zipfile
import json
from resilient_circuits.util.ext.ExtCreate import PREFIX_EXTENSION_ZIP
from resilient_circuits.util.ext import ExtPackage, ExtException

# Import mock_data (need to add path to support relative imports in PY3)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ext_tests.mock_data import mock_data

path_this_dir = os.path.dirname(os.path.realpath(__file__))
path_temp_test_dir = os.path.join(path_this_dir, "test_temp")
path_fn_mock_integration = os.path.join(path_this_dir, "mock_data", "fn_mock_integration")
path_fn_mock_integration_dist_dir = os.path.join(path_this_dir, "mock_data", "fn_mock_integration", "dist")

path_mock_extension_json = os.path.join(path_this_dir, "mock_data", "ext-fn_mock_integration-1.0.0", "extension.json")
path_mock_extension_json_custom_display_name = os.path.join(path_this_dir, "mock_data", "ext-fn_mock_integration-1.0.0", "extension_custom_display_name.json")


def get_dict_from_json_file(file_path):
    dict_to_return = {}
    with open(file_path, 'r') as the_file:
            dict_to_return = json.load(the_file)
    return dict_to_return


class ExtPackageClassTestPackageExtension(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        self.ext_creator = ExtPackage("ext:package")

        # Create temp dir
        os.makedirs(path_temp_test_dir)

    def tearDown(self):
        # Remove dist dir
        shutil.rmtree(path_fn_mock_integration_dist_dir, ignore_errors=True)

        # Remove temp dir
        shutil.rmtree(path_temp_test_dir, ignore_errors=True)

    def validate_extension_json(self, path_the_extension_zip, path_mock_extension_json):

        # Get the mock data
        mock_extension_json = get_dict_from_json_file(path_mock_extension_json)

        # Extract the zip
        with zipfile.ZipFile(file=path_the_extension_zip, mode="r") as zip_file:
            zip_file.extractall(path=path_temp_test_dir)

        # Get the extension_json
        extension_json = get_dict_from_json_file(os.path.join(path_temp_test_dir, "extension.json"))

        # Compare
        self.assertEqual(mock_extension_json, extension_json)

    def test_package_extension_no_params(self):
        # Generate names for .zip and .tar.gz files that will be created
        expected_extension_zip_name = "{0}{1}-{2}.zip".format(PREFIX_EXTENSION_ZIP, mock_data.MOCK_INTEGRATION_NAME, mock_data.MOCK_INTEGRATION_VERSION)
        expected_built_distribution_name = "{0}-{1}.tar.gz".format(mock_data.MOCK_INTEGRATION_NAME, mock_data.MOCK_INTEGRATION_VERSION)

        # List of files expected in the dist dir
        expected_dist_dir_contents = [
            expected_extension_zip_name,
            expected_built_distribution_name
        ]

        # Expected path to the created extension.zip
        expected_path_the_extension_zip = os.path.join(path_fn_mock_integration_dist_dir, expected_extension_zip_name)

        # Package the fn_mock_integration
        path_the_extension_zip = self.ext_creator.package_extension(path_fn_mock_integration)
        dist_dir_contents = os.listdir(path_fn_mock_integration_dist_dir)

        # Compare
        self.assertEqual(path_the_extension_zip, expected_path_the_extension_zip)
        self.assertEqual(dist_dir_contents, expected_dist_dir_contents)

        # Validate the extension.json
        self.validate_extension_json(path_the_extension_zip, path_mock_extension_json)

    def test_package_extension_keep_build_dir_true(self):
        # Package the fn_mock_integration
        self.ext_creator.package_extension(
            path_to_src=path_fn_mock_integration,
            keep_build_dir=True)

        # Check the build dir still exists
        self.assertTrue(os.path.exists(os.path.join(path_fn_mock_integration_dist_dir, "build")))

    def test_package_extension_keep_build_dir_false(self):
        # Package the fn_mock_integration
        self.ext_creator.package_extension(
            path_to_src=path_fn_mock_integration,
            keep_build_dir=False)

        # Check the build dir does not exist
        self.assertFalse(os.path.exists(os.path.join(path_fn_mock_integration_dist_dir, "build")))

    def test_package_extension_custom_display_name(self):
        # Package the fn_mock_integration
        path_the_extension_zip = self.ext_creator.package_extension(
            path_to_src=path_fn_mock_integration,
            custom_display_name="Mock Custom Display Name")

        # Validate the extension.json
        self.validate_extension_json(path_the_extension_zip, path_mock_extension_json_custom_display_name)
