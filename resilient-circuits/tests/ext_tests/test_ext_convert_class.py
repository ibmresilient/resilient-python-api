import unittest
import os
import sys
from resilient_circuits.util.ext.ExtCreate import PREFIX_EXTENSION_ZIP
from resilient_circuits.util.ext import ExtConvert, ExtException

# Import mock_data (need to add path to support relative imports in PY3)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ext_tests.mock_data import mock_data

path_this_dir = os.path.dirname(os.path.realpath(__file__))
path_temp_test_dir = os.path.join(path_this_dir, "test_temp")
path_mock_built_distributions = os.path.join(path_this_dir, "mock_data", "built_distributions")

path_mock_bd_true_tar = os.path.join(path_mock_built_distributions, "true_tar_fn_mock_integration-1.0.0.tar.gz")
path_mock_bd_true_zip = os.path.join(path_mock_built_distributions, "true_zip_fn_mock_integration-1.0.0.zip")
path_mock_bd_zipped_tar = os.path.join(path_mock_built_distributions, "zipped_tar_fn_mock_integration-1.0.0.zip")
path_mock_bd_zipped_tar_in_sub_folder = os.path.join(path_mock_built_distributions, "zipped_tar_in_sub_folder.zip")
path_mock_bd_corrupt_tar = os.path.join(path_mock_built_distributions, "mock_corrupt_tar.tar.gz")
path_mock_bd_zipped_tar_corrupt = os.path.join(path_mock_built_distributions, "zipped_tar_corrupt.zip")
path_mock_setup_py = os.path.join(path_this_dir, "mock_data", "fn_mock_integration", "setup.py")

# Generate name and path for .zip that is expected to be created when convert completes
expected_extension_zip_name = "{0}{1}-{2}.zip".format(PREFIX_EXTENSION_ZIP, mock_data.MOCK_INTEGRATION_NAME, mock_data.MOCK_INTEGRATION_VERSION)
expected_path_the_extension_zip = os.path.join(path_mock_built_distributions, expected_extension_zip_name)


class ExtConvertClassTestConvertExtension(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        # assertRaisesRegexp renamed to assertRaisesRegex in PY3.2
        if sys.version_info < (3, 2):
            self.assertRaisesRegex = self.assertRaisesRegexp

        self.ext_creator = ExtConvert("ext:convert")

    def tearDown(self):
        # Remove the extension.zip if its created
        if os.path.exists(expected_path_the_extension_zip):
            os.remove(expected_path_the_extension_zip)

    def test_convert_true_tar(self):
        # Convert the built distribution
        path_the_extension_zip = self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_true_tar)

        self.assertTrue(os.path.exists(path_the_extension_zip))
        self.assertEqual(path_the_extension_zip, expected_path_the_extension_zip)

    def test_convert_true_zip(self):
        # Convert the built distribution
        path_the_extension_zip = self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_true_zip)

        self.assertTrue(os.path.exists(path_the_extension_zip))
        self.assertEqual(path_the_extension_zip, expected_path_the_extension_zip)

    def test_convert_zipped_tar(self):
        # Convert the built distribution
        path_the_extension_zip = self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_zipped_tar)

        self.assertTrue(os.path.exists(path_the_extension_zip))
        self.assertEqual(path_the_extension_zip, expected_path_the_extension_zip)

    def test_convert_zipped_tar_in_sub_folder(self):
        # Convert the built distribution
        path_the_extension_zip = self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_zipped_tar_in_sub_folder)

        self.assertTrue(os.path.exists(path_the_extension_zip))
        self.assertEqual(path_the_extension_zip, expected_path_the_extension_zip)

    def test_convert_corrupt_tar(self):
        # Convert the built distribution
        with self.assertRaisesRegex(ExtException, "Invalid built distribution"):
            self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_corrupt_tar)

    def test_convert_zipped_tar_corrupt(self):
        # Convert the built distribution
        with self.assertRaisesRegex(ExtException, "Could not extract required files from given Built Distribution"):
            self.ext_creator.convert_to_extension(path_built_distribution=path_mock_bd_zipped_tar_corrupt)

    def test_convert_directory(self):
        # Try convert by passing a path to a directory
        with self.assertRaisesRegex(ExtException, "You must specify a Built Distribution. Not a Directory"):
            self.ext_creator.convert_to_extension(path_built_distribution=path_mock_built_distributions)

    def test_convert_file(self):
        # Try convert by passing a path to a file
        with self.assertRaisesRegex(ExtException, "Invalid Built Distribution provided"):
            self.ext_creator.convert_to_extension(path_built_distribution=path_mock_setup_py)
