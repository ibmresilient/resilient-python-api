import unittest
import os
import sys
import shutil
import stat
from resilient_circuits.util.ext.Ext import Ext
from resilient_circuits.util.ext import ExtException


class ExtClassTestIndividualFns(unittest.TestCase):

    def setUp(self):
        # assertRaisesRegexp renamed to assertRaisesRegex in PY3.2
        if sys.version_info < (3, 2):
            self.assertRaisesRegex = self.assertRaisesRegexp

        self.ext_class = Ext("ext:package")
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.temp_dir = os.path.join(self.dir_path, "test_temp")
        self.mock_file_contents = "Write this to mock file"
        os.makedirs(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_read_write_file(self):

        temp_file = os.path.join(self.temp_dir, "mock_file.txt")

        self.ext_class.__write_file__(temp_file, self.mock_file_contents)
        self.assertTrue(os.path.isfile(temp_file))

        file_lines = self.ext_class.__read_file__(temp_file)
        self.assertIn(self.mock_file_contents, file_lines)

    def test_has_permissions(self):
        temp_permissions_file = os.path.join(self.temp_dir, "mock_permissions.txt")
        self.ext_class.__write_file__(temp_permissions_file, self.mock_file_contents)

        # Set permissions to Read only
        os.chmod(temp_permissions_file, stat.S_IRUSR)

        with self.assertRaisesRegex(ExtException, "User does not have WRITE permissions"):
            self.ext_class.__has_permissions__(os.W_OK, temp_permissions_file)

        # Set permissions to Write only
        os.chmod(temp_permissions_file, stat.S_IWUSR)

        with self.assertRaisesRegex(ExtException, "User does not have READ permissions"):
            self.ext_class.__has_permissions__(os.R_OK, temp_permissions_file)

    def test_validate_directory(self):

        non_exist_path = "/non_exits/path"

        with self.assertRaisesRegex(ExtException, "The path does not exist: " + non_exist_path):
            self.ext_class.__validate_directory__(os.R_OK, non_exist_path)

        exists_dir = os.path.join(self.temp_dir, "mock_existing_dir")
        os.makedirs(exists_dir)

        self.ext_class.__validate_directory__(os.R_OK, exists_dir)

    def test_validate_file_paths(self):

        non_exist_path = "/non_exits/path"
        with self.assertRaisesRegex(ExtException, "Could not find file: " + non_exist_path):
            self.ext_class.__validate_file_paths__(None, non_exist_path)

        exists_file = os.path.join(self.temp_dir, "mock_existing_file.txt")
        self.ext_class.__write_file__(exists_file, self.mock_file_contents)

        self.ext_class.__validate_file_paths__(None, exists_file)

    def test_is_valid_url(self):
        self.assertTrue(self.ext_class.__is_valid_url__("www.example.com"))
        self.assertTrue(self.ext_class.__is_valid_url__("example.com"))
        self.assertTrue(self.ext_class.__is_valid_url__("http://www.example.com"))
        self.assertTrue(self.ext_class.__is_valid_url__("https://www.example.com"))

        self.assertFalse(self.ext_class.__is_valid_url__(None))
        self.assertFalse(self.ext_class.__is_valid_url__("not a url"))
        self.assertFalse(self.ext_class.__is_valid_url__("https://www. example.com"))

    def test_is_valid_package_name(self):
        self.assertTrue(self.ext_class.__is_valid_package_name__("fn_valid_name"))
        self.assertTrue(self.ext_class.__is_valid_package_name__("fn_VALID"))
        self.assertTrue(self.ext_class.__is_valid_package_name__("fn"))
        self.assertTrue(self.ext_class.__is_valid_package_name__("fn_valid_name_123"))

        self.assertFalse(self.ext_class.__is_valid_package_name__("fn-not-valid"))
        self.assertFalse(self.ext_class.__is_valid_package_name__("fn -not-valid"))
        self.assertFalse(self.ext_class.__is_valid_package_name__("fn_!@#_not_valid"))

    def test_generate_uuid_from_string(self):
        the_string, the_uuid = "fn_test_package", "7627eab9-8500-cf1d-380d-14a2c4364acf"

        the_generated_uuid = self.ext_class.__generate_uuid_from_string__(the_string)

        self.assertEqual(the_generated_uuid, the_uuid)
