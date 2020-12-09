import argparse
from argparse import Namespace
from shutil import rmtree

import pytest
from mock import patch
from pkg_resources import EggInfoDistribution, EntryPoint

from resilient import get_config_file
from resilient_circuits.bin.resilient_circuits_cmd import *
from tests.shared_mock_data import mock_paths


DEFAULT_CONFIG_FILENAME = "app.config"
DEFAULT_CONFIG_FILE = os.path.expanduser(
    os.path.join("~", ".resilient", DEFAULT_CONFIG_FILENAME))

MOCKED_SELFTEST_ENTRYPOINTS = [EntryPoint.parse('test = tests.selftest_tests.mocked_fail_script:selftest', dist=EggInfoDistribution(
    project_name='test',
    version="0.1",
)), EntryPoint.parse('test2 = tests.selftest_tests.mocked_success_script:selftest', dist=EggInfoDistribution(
    project_name='test2',
    version="0.1"))]


def mock_os_path_exists(path):
    return True


def mock_makedirs(dir):
    pass


class TestGetConfigGenerate(object):

    @pytest.fixture(scope='session')
    def tmp_config_file(self, tmpdir_factory):
        tmp_config_dir = tmpdir_factory.mktemp(".resilient")
        tmp_config_file = os.path.expanduser(os.path.join(
            str(tmp_config_dir), DEFAULT_CONFIG_FILENAME))
        yield tmp_config_file
        rmtree(str(tmp_config_dir))

    def test_generate_with_env_variable(self, monkeypatch, tmp_config_file):
        """
        Test generate with environment variable $APP_CONFIG_FILE.
        """
        monkeypatch.setenv("APP_CONFIG_FILE", str(tmp_config_file))
        result = get_config_file(generate_filename=True)
        assert result == tmp_config_file

    def test_generate_with_filename(self):
        """
        Test generate with filename specified.
        """
        test_file_name = "test_file"
        result = get_config_file(
            filename=test_file_name, generate_filename=True)
        assert result == test_file_name

    @patch('resilient.co3.os.path.exists', side_effect=mock_os_path_exists)
    def test_generate_with_app_config_path_exists(self, mock_os_path_exists):
        """
        Test with default and file exists.
        """
        result = get_config_file(generate_filename=True)
        assert result == DEFAULT_CONFIG_FILE

    @patch('resilient.co3.os.makedirs', side_effect=mock_makedirs)
    def test_generate_with_dot_make_dir(self, mock_os_makedirs):
        """
        Test app.config in "~/.resilient dir with make dir.
        """
        result = get_config_file(generate_filename=True)
        assert result == DEFAULT_CONFIG_FILE


class TestSelfTest(object):

    def test_selftest_exits_on_test_failure(self):
        """
        Test that when selftest is called and a selftest function fails or raises an exception
        that the program exits and gives an error code of 15
        """
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            parser = Namespace(install_list=['test'], project_name=['test'])

            with patch("resilient_circuits.bin.resilient_circuits_cmd.pkg_resources.iter_entry_points", create=True) as mocked_entrypoints:
                mocked_entrypoints.return_value = MOCKED_SELFTEST_ENTRYPOINTS
                with patch("resilient_circuits.bin.resilient_circuits_cmd.resilient.get_config_file") as mocked_config:
                    mocked_config.return_value = mock_paths.MOCK_APP_CONFIG
                    selftest(parser)

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_selftest_passes_on_test_success(self):
        """
        Test a full run through of selftest with only passing selftest functions
        After calling selftest no exceptions should be raised
        """
        parser = Namespace(install_list=['test2'], project_name=['test2'])

        with patch("resilient_circuits.bin.resilient_circuits_cmd.pkg_resources.iter_entry_points", create=True) as mocked_entrypoints:
            mocked_entrypoints.return_value = [MOCKED_SELFTEST_ENTRYPOINTS[1]]
            with patch("resilient_circuits.bin.resilient_circuits_cmd.resilient.get_config_file") as mocked_config:
                mocked_config.return_value = mock_paths.MOCK_APP_CONFIG
                selftest(parser)
