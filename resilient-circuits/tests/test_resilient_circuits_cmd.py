#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

from shutil import rmtree
import pytest
from mock import patch
from resilient import get_config_file
from resilient_circuits.bin.resilient_circuits_cmd import *


DEFAULT_CONFIG_FILENAME = "app.config"
DEFAULT_CONFIG_FILE = os.path.expanduser(
    os.path.join("~", ".resilient", DEFAULT_CONFIG_FILENAME))


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
