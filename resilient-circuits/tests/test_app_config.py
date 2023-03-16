#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import copy
import sys

import pytest
from resilient_circuits.app import AppArgumentParser
from resilient_circuits.validate_configs import (MAX_NUM_WORKERS,
                                                 MIN_BACKUP_COUNT,
                                                 MIN_LOG_BYTES)
from tests.shared_mock_data import mock_paths


def test_num_workers(fx_clear_cmd_line_args):

    # Test reading from app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 50

    # Test default value - commented out in app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_COMMENTED_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 25

    # Test overwriting
    sys.argv.extend(["--num-workers", "30"])
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 30

    # Test if over limit
    sys.argv.extend(["--num-workers", str(MAX_NUM_WORKERS+1)])
    with pytest.raises(ValueError, match=r"num_workers must be in the range .*"):
        AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()


def test_global_integrations_options(fx_clear_cmd_line_args):
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args().get("integrations", {})
    assert opts.get("http_proxy") == "http://example.com:3000"
    assert opts.get("https_proxy") == "https://example.com:3000"
    assert opts.get("timeout") == "50"


def test_global_integrations_options_commented_out(fx_clear_cmd_line_args):
    opts = AppArgumentParser(config_file=mock_paths.MOCK_COMMENTED_APP_CONFIG).parse_args().get("integrations", {})
    assert opts.get("http_proxy") is None
    assert opts.get("https_proxy") is None
    assert opts.get("timeout") is None


def test_log_max_bytes_settings(fx_clear_cmd_line_args):

    # Test reading from app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_max_bytes"), int)
    assert opts.get("log_max_bytes") == 20000000

    # Test default value - commented out in app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_COMMENTED_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_max_bytes"), int)
    assert opts.get("log_max_bytes") == AppArgumentParser.DEFAULT_LOG_MAX_BYTES # default

    # Test overwriting
    sys.argv.extend(["--log_max_bytes", "30000000"])
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_max_bytes"), int)
    assert opts.get("log_max_bytes") == 30000000

    # Test if over limit
    sys.argv.extend(["--log_max_bytes", str(MIN_LOG_BYTES-1)])
    with pytest.raises(ValueError, match=r"log_max_bytes must be either 0 or >= .*"):
        AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()


def test_log_backup_count_settings(fx_clear_cmd_line_args):

    # Test reading from app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_backup_count"), int)
    assert opts.get("log_backup_count") == 11

    # Test default value - commented out in app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_COMMENTED_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_backup_count"), int)
    assert opts.get("log_backup_count") == AppArgumentParser.DEFAULT_LOG_BACKUP_COUNT # default

    # Test overwriting
    sys.argv.extend(["--log_backup_count", "5"])
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("log_backup_count"), int)
    assert opts.get("log_backup_count") == 5

    # Test if over limit
    sys.argv.extend(["--log_backup_count", str(MIN_BACKUP_COUNT-1)])
    with pytest.raises(ValueError, match="log_backup_count must be a positive value"):
        AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()

