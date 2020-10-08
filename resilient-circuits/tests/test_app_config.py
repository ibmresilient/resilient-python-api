#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import copy
import sys
import pytest
from resilient_circuits.app import AppArgumentParser
from tests.shared_mock_data import mock_paths


def test_num_workers(fx_clear_cmd_line_args):

    # Test reading from app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 5

    # Test default value - commented out in app.config
    opts = AppArgumentParser(config_file=mock_paths.MOCK_COMMENTED_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 10

    # Test overwriting
    sys.argv.extend(["--num-workers", "30"])
    opts = AppArgumentParser(config_file=mock_paths.MOCK_APP_CONFIG).parse_args()
    assert isinstance(opts.get("num_workers"), int)
    assert opts.get("num_workers") == 30
