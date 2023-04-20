#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import logging

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