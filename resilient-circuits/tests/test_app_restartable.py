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


def test_reload_config_not_already_loading():
    magic_app = MagicMock()
    config_update_handler = ConfigFileUpdateHandler(magic_app)
    with patch("resilient_circuits.app_restartable.AppArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = {"loglevel": "DEBUG"}
        magic_app.reloading = False
        magic_app.config_file = None
        config_update_handler.reload_config()
        assert config_update_handler.app.reloading

def test_reload_config_is_already_loading():
    magic_app = MagicMock()
    config_update_handler = ConfigFileUpdateHandler(magic_app)
    with patch("resilient_circuits.app_restartable.AppArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = {"loglevel": "DEBUG"}
        magic_app.reloading = True
        config_update_handler.reload_config()
        assert config_update_handler.app.reloading


def test_reset_loglevel():
    config_update_handler = ConfigFileUpdateHandler(MagicMock())
    assert logging.getLevelName(logging.getLogger().level) == "DEBUG" # NOTE: this always work locally, but when run in Tox, this is the log level here

    opts = {"loglevel": "INFO"}
    config_update_handler.reset_loglevel(opts)
    assert logging.getLevelName(logging.getLogger().level) == "INFO"


@pytest.mark.parametrize("app_config_data, hash", [
    ("Test data 1", "f6804dad29083da6a0a6308580507d4fe06ba469c92a4cdb5cde6420aaff57d8"),
    ("Dummy config 2", "c180c51c78e96a14812cb340b1f72b7a0ebaf3c9197f0aa1c807521065b9c98b"),
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
