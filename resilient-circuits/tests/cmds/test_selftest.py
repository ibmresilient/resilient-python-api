#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from mock import patch
from argparse import Namespace
from pkg_resources import EggInfoDistribution, EntryPoint
from resilient_circuits import helpers
from resilient_circuits.cmds import selftest
from tests.shared_mock_data import mock_paths


MOCKED_SELFTEST_ENTRYPOINTS = [EntryPoint.parse('test = tests.selftest_tests.mocked_fail_script:selftest', dist=EggInfoDistribution(
    project_name='test',
    version="0.1",
)), EntryPoint.parse('test2 = tests.selftest_tests.mocked_success_script:selftest', dist=EggInfoDistribution(
    project_name='test2',
    version="0.1"))]


def test_error_connecting_to_soar_rest(caplog):
    with pytest.raises(SystemExit) as sys_exit:
        selftest.error_connecting_to_soar("mock_host", status_code=20)

    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == 20


def test_check_soar_rest_connection():
    # TODO
    pass


def test_check_soar_stomp_connection():
    # TODO
    pass


def test_run_apps_selftest_success():
    """
    Test a full run through of selftest with only passing selftest functions
    After calling selftest no exceptions should be raised
    """
    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)
    parser = Namespace(install_list=['test2'], project_name=['test2'])

    with patch("resilient_circuits.bin.resilient_circuits_cmd.pkg_resources.iter_entry_points", create=True) as mocked_entrypoints:
        mocked_entrypoints.return_value = [MOCKED_SELFTEST_ENTRYPOINTS[1]]
        with patch("resilient_circuits.bin.resilient_circuits_cmd.get_config_file") as mocked_config:
            mocked_config.return_value = mock_paths.MOCK_APP_CONFIG
            selftest.run_apps_selftest(parser, app_configs)


def test_run_apps_selftest_failure():
    """
    Test that when selftest is called and a selftest function fails or raises an exception
    that the program exits and gives an error code of 1
    """

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser = Namespace(install_list=['test'], project_name=['test'])

        with patch("resilient_circuits.cmds.selftest.pkg_resources.iter_entry_points", create=True) as mocked_entrypoints:
            mocked_entrypoints.return_value = MOCKED_SELFTEST_ENTRYPOINTS
            selftest.run_apps_selftest(parser, app_configs)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
