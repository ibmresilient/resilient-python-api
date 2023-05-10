#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import logging
from argparse import Namespace

import pytest
from mock import patch
from pkg_resources import EggInfoDistribution, EntryPoint
from resilient_circuits import helpers
from resilient_circuits.cmds import selftest
from tests.shared_mock_data import mock_paths
from resilient_app_config_plugins import Keyring

MOCKED_SELFTEST_ENTRYPOINTS = [
    EntryPoint.parse('test = tests.selftest_tests.mocked_fail_script:selftest', dist=EggInfoDistribution(
        project_name='test',
        version="0.1",
    )), 
    EntryPoint.parse('test2 = tests.selftest_tests.mocked_success_script:selftest', dist=EggInfoDistribution(
        project_name='test2',
        version="0.1"
    )),
    EntryPoint.parse('test3 = tests.selftest_tests.mocked_unimplemented_script:selftest', dist=EggInfoDistribution(
        project_name='test3',
        version="0.1"
    ))
]


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

def test_run_apps_selftest_unimplemented():
    """
    Test that when selftest is called and the app's selftest function returns 
    unimplemented, that the circuits cmd exists and gives an error code of 2
    """

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        parser = Namespace(install_list=['test3'], project_name=['test3'])

        with patch("resilient_circuits.cmds.selftest.pkg_resources.iter_entry_points", create=True) as mocked_entrypoints:
            mocked_entrypoints.return_value = [MOCKED_SELFTEST_ENTRYPOINTS[2]]
            selftest.run_apps_selftest(parser, app_configs)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

def test_run_check_pam_plugin_selftest_has_no_plugin(caplog):

    caplog.set_level(logging.INFO)

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    del app_configs.pam_plugin

    selftest.check_pam_plugin_selftest(app_configs)

    assert "No Plugin specified" in caplog.text

def test_run_check_pam_plugin_selftest_not_implemented(caplog):

    caplog.set_level(logging.INFO)

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    with patch.object(Keyring, "selftest") as patch_selftest:
        patch_selftest.side_effect = NotImplementedError()
        selftest.check_pam_plugin_selftest(app_configs)

    assert "PAM Plugin selftest not implemented" in caplog.text

def test_run_check_pam_plugin_selftest_unknown_error(caplog):

    caplog.set_level(logging.INFO)

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    with patch.object(Keyring, "selftest") as patch_selftest:
        patch_selftest.side_effect = Exception("some error")
        selftest.check_pam_plugin_selftest(app_configs)

    assert "Unknown error while running PAM Plugin selftest: some error" in caplog.text

def test_run_check_pam_plugin_selftest_returns_not_tuple(caplog):

    caplog.set_level(logging.INFO)

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    with patch.object(Keyring, "selftest") as patch_selftest:
        patch_selftest.return_value = False
        with pytest.raises(SystemExit):
            selftest.check_pam_plugin_selftest(app_configs)

    assert "ERROR: PAM Plugin test failed. Reason: REASON UNKNOWN" in caplog.text

def test_run_check_pam_plugin_selftest_normal(caplog):

    caplog.set_level(logging.INFO)

    app_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG, ALLOW_UNRECOGNIZED=True)

    selftest.check_pam_plugin_selftest(app_configs)

    assert "PAM Plugin correctly configured" in caplog.text
