#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import logging
import os
import time
from watchdog.observers import Observer
import pytest

from mock import MagicMock, patch
from resilient_circuits.app_restartable import ConfigFileUpdateHandler

from tests.shared_mock_data import mock_paths

def get_mock_app_cnfig():
    with open(mock_paths.MOCK_APP_CONFIG) as f:
        return f.read()

@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.get_config_file_hash', return_value=MagicMock())
def test_reload_config_not_already_loading(get_config_file_hash_mock):
    magic_app = MagicMock()
    config_update_handler = ConfigFileUpdateHandler(magic_app)
    with patch("resilient_circuits.app_restartable.AppArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = {"loglevel": "DEBUG"}
        magic_app.reloading = False
        magic_app.config_file = None
        config_update_handler.reload_config()
        assert config_update_handler.app.reloading

@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.get_config_file_hash', return_value=MagicMock())
def test_reload_config_is_already_loading(get_config_file_hash_mock):
    magic_app = MagicMock()
    config_update_handler = ConfigFileUpdateHandler(magic_app)
    with patch("resilient_circuits.app_restartable.AppArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = {"loglevel": "DEBUG"}
        magic_app.reloading = True
        config_update_handler.reload_config()
        assert config_update_handler.app.reloading

@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.get_config_file_hash', return_value=MagicMock())
def test_reset_loglevel(get_config_file_hash_mock):
    config_update_handler = ConfigFileUpdateHandler(MagicMock())
    assert logging.getLevelName(logging.getLogger().level) == "DEBUG" # NOTE: this always work locally, but when run in Tox, this is the log level here

    opts = {"loglevel": "INFO"}
    config_update_handler.reset_loglevel(opts)
    assert logging.getLevelName(logging.getLogger().level) == "INFO"


@pytest.mark.parametrize("app_config_data, hash", [
    ("", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("Test data 1", "f6804dad29083da6a0a6308580507d4fe06ba469c92a4cdb5cde6420aaff57d8"),
    (get_mock_app_cnfig(), "b231226b3c66e650ac2e62e40dae8af308aa10a4b109a5e4b39c9c1e72d5051a")

])
def test_get_config_file_hash(fx_config_file, app_config_data, hash):
    app = MagicMock()
    with open(fx_config_file, "w") as config_f:
        config_f.write(app_config_data)

    app.config_file  = fx_config_file
    config_update_handler = ConfigFileUpdateHandler(app)
    ConfigFileUpdateHandler.set_patterns(fx_config_file)
    assert config_update_handler.get_config_file_hash() == hash


@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.on_closed', return_value=MagicMock())
def test_on_any_event(on_closed_mock, fx_config_file):
    app = MagicMock()
    app.config_file = fx_config_file
    with open(fx_config_file, "w") as config_f:
        config_f.write("Initial data")
    # Setup watchdog
    ConfigFileUpdateHandler.set_patterns(fx_config_file)
    event_handler = ConfigFileUpdateHandler(app)
    event_handler.reload_config = MagicMock
    app.observer = Observer()
    config_dir = os.path.dirname(fx_config_file)

    app.observer.schedule(event_handler, path=config_dir, recursive=False)
    app.observer.daemon = True
    app.observer.start()
    # Do tests
    assert event_handler.app_config_file_events == []
    with open(fx_config_file, "r") as config_f:
        config_f.read()
    time.sleep(1)
    assert event_handler.app_config_file_events == ["opened"]
    on_closed_mock.assert_not_called()
    with open(fx_config_file, "w") as config_f:
        config_f.write("Write event")
    time.sleep(1)
    assert event_handler.app_config_file_events == ["modified", "closed"]
    on_closed_mock.assert_called()
    with open(fx_config_file, "r") as config_f:
        config_f.read()
    time.sleep(1)
    assert event_handler.app_config_file_events == ["closed", "opened"]
    on_closed_mock.call_count == 1
    with open(fx_config_file, "w") as config_f:
        config_f.write("Write event")
    time.sleep(1)
    assert event_handler.app_config_file_events == ["modified", "closed"]
    on_closed_mock.call_count == 2

@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.on_closed', return_value=MagicMock())
def test_on_any_event_with_app_config(on_closed_mock, fx_config_file):
    app = MagicMock()
    app.config_file = fx_config_file
    with open(mock_paths.MOCK_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    # Setup watchdog
    ConfigFileUpdateHandler.set_patterns(fx_config_file)
    event_handler = ConfigFileUpdateHandler(app)
    event_handler.reload_config = MagicMock
    app.observer = Observer()
    config_dir = os.path.dirname(fx_config_file)

    app.observer.schedule(event_handler, path=config_dir, recursive=False)
    app.observer.daemon = True
    app.observer.start()
    # Do tests
    assert event_handler.app_config_file_events == []
    with open(fx_config_file, "r") as config_f:
        config_f.read()
    time.sleep(1)
    assert event_handler.app_config_file_events == ["opened"]
    on_closed_mock.assert_not_called()
    #Rewrite config file
    with open(mock_paths.MOCK_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    time.sleep(1)
    assert event_handler.app_config_file_events == ["modified", "closed"]
    on_closed_mock.assert_called()
    with open(fx_config_file, "r") as config_f:
        config_f.read()
    time.sleep(1)
    assert event_handler.app_config_file_events == ["closed", "opened"]
    on_closed_mock.call_count == 1
    #Write new config file
    with open(mock_paths.MOCK_COMMENTED_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    time.sleep(1)
    assert event_handler.app_config_file_events == ["modified", "closed"]
    on_closed_mock.call_count == 2


@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.reload_config', return_value=MagicMock())
def test_on_closed(reload_config_mock, fx_config_file):
    app = MagicMock()
    app.config_file = fx_config_file
    with open(fx_config_file, "w") as config_f:
        config_f.write("Initial data")
    # Setup watchdog
    ConfigFileUpdateHandler.set_patterns(fx_config_file)
    event_handler = ConfigFileUpdateHandler(app)
    app.observer = Observer()
    config_dir = os.path.dirname(fx_config_file)

    app.observer.schedule(event_handler, path=config_dir, recursive=False)
    app.observer.daemon = True
    app.observer.start()
    # Do tests
    assert event_handler.config_file_hash == "d7b5a395d30891832f39f0ac8c6cad75e839965afc645f03838eb133e60976c6"
    with open(fx_config_file, "w") as config_f:
        config_f.write("Initial data")
    time.sleep(1)
    assert event_handler.config_file_hash == "d7b5a395d30891832f39f0ac8c6cad75e839965afc645f03838eb133e60976c6"
    reload_config_mock.assert_not_called()
    with open(fx_config_file, "w") as config_f:
        config_f.write("Write event")
    time.sleep(1)
    assert event_handler.config_file_hash == "275cc1e568d4b94bd532ee8f03424f5e4d2b8e5e0018a7834356fd46d2165816"
    reload_config_mock.assert_called()
    with open(fx_config_file, "w") as config_f:
        config_f.write("Write event")
    time.sleep(1)
    assert event_handler.config_file_hash == "275cc1e568d4b94bd532ee8f03424f5e4d2b8e5e0018a7834356fd46d2165816"
    assert reload_config_mock.call_count == 1
    with open(fx_config_file, "w") as config_f:
        config_f.write("Write event update")
    time.sleep(1)
    assert event_handler.config_file_hash == "9fd2b669cec7225c076e6be65a65e162a8bee06eedbebc33b98e51c007269178"
    assert reload_config_mock.call_count == 2

@patch('resilient_circuits.app_restartable.ConfigFileUpdateHandler.reload_config', return_value=MagicMock())
def test_on_closed_with_app_config(reload_config_mock, fx_config_file):
    app = MagicMock()
    app.config_file = fx_config_file
    # Write app_config data to temp file
    with open(mock_paths.MOCK_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    # Setup watchdog
    ConfigFileUpdateHandler.set_patterns(fx_config_file)
    event_handler = ConfigFileUpdateHandler(app)
    app.observer = Observer()
    config_dir = os.path.dirname(fx_config_file)

    app.observer.schedule(event_handler, path=config_dir, recursive=False)
    app.observer.daemon = True
    app.observer.start()
    # Do tests
    assert event_handler.config_file_hash == "b231226b3c66e650ac2e62e40dae8af308aa10a4b109a5e4b39c9c1e72d5051a"
    #Rewrite config file
    with open(mock_paths.MOCK_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    time.sleep(1)
    assert event_handler.config_file_hash == "b231226b3c66e650ac2e62e40dae8af308aa10a4b109a5e4b39c9c1e72d5051a"
    reload_config_mock.assert_not_called()
    #Write new config file
    with open(mock_paths.MOCK_COMMENTED_APP_CONFIG) as f:
        app_config_content = f.read()
        with open(fx_config_file, "w") as config_f:
            config_f.write(app_config_content)
    time.sleep(1)
    assert event_handler.config_file_hash == "8739a9309277f4af04fac3aea0f3a135639ce4d45c19661514c449de376ef92a"
    reload_config_mock.assert_called()
