#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.


import argparse
import sys

import pkg_resources
import pytest
import resilient_sdk.app as app
from mock import MagicMock, patch
from resilient_sdk.util import constants


def test_get_main_app_parser():
    # Append to command line arguments, using sys.argv.append()
    sys.argv.append("-v")

    parser = app.get_main_app_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.description == """Python SDK for developing IBM SOAR Apps that
        provides various subcommands to help with development"""
    assert parser.epilog == "For support, please visit https://ibm.biz/soarcommunity"

    args = parser.parse_known_args()[0]

    assert args.verbose is True


def test_get_main_app_sub_parser():
    main_parser = app.get_main_app_parser()
    sub_parser = app.get_main_app_sub_parser(main_parser)

    assert sub_parser.dest == "cmd"
    assert sub_parser.container.description == "one of these subcommands must be provided"
    assert sub_parser.container.title == "subcommands"


@pytest.mark.skipif(sys.version_info < constants.MIN_SUPPORTED_PY_VERSION, reason="requires python3.6 or higher")
@patch.multiple("resilient_sdk.app.sdk_helpers",
                get_resilient_sdk_version=MagicMock(return_value=pkg_resources.parse_version("40.0.0")),
                get_latest_available_version=MagicMock(return_value=pkg_resources.parse_version("41.0.0")))
def test_main_print_version_warning(caplog):

    with pytest.raises(SystemExit):
        app.main()

    msg = "WARNING:\n'40.0.0' is not the latest version of the resilient-sdk. \
'v41.0.0' is available on https://pypi.org/project/resilient-sdk/\n\n\
To update run:\n\t$ pip install -U resilient-sdk"

    assert msg in caplog.text
