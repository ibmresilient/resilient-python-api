import pytest
from mock import patch
from shutil import rmtree
from resilient_circuits.bin.resilient_circuits_cmd import *

def mock_os_path_exists(path):
    return True

def mock_makedirs(dir):
    pass

class TestGetConfigName(object):

    @pytest.fixture(scope='session')
    def tmp_config_file(self, tmpdir_factory):
        default_filename = "app.config"
        tmp_config_dir = tmpdir_factory.mktemp(".resilient")
        tmp_config_file = os.path.expanduser(os.path.join(tmp_config_dir, default_filename))
        yield tmp_config_file
        rmtree(str(tmp_config_dir))

    def test_with_env_variable(self, monkeypatch, tmp_config_file):
        """
        Test with environment variable $APP_CONFIG_FILE.
        """
        monkeypatch.setenv("APP_CONFIG_FILE", str(tmp_config_file))
        result = get_config_file_name()
        assert result == tmp_config_file

    def test_with_filename(self):
        """
        Test with filename specified.
        """
        test_file_name = "test_file"
        result = get_config_file_name(filename=test_file_name)
        assert result == test_file_name

    @patch('resilient_circuits.bin.resilient_circuits_cmd.os.path.exists', side_effect=mock_os_path_exists)
    def test_with_app_config(self, mock_os_path_exists):
        """
        Test with app.config in local path.
        """
        default_filename = "app.config"
        result = get_config_file_name()
        assert result == default_filename

    @patch('resilient_circuits.bin.resilient_circuits_cmd.os.makedirs', side_effect=mock_makedirs)
    def test_with_dot_resilient_dir(self, mock_os_makedirs):
        """
        Test app.config in "~/.resilient dir.
        """
        default_filename = "app.config"
        default_test_file = os.path.expanduser(os.path.join("~", ".resilient", default_filename))
        result = get_config_file_name()
        assert result == default_test_file