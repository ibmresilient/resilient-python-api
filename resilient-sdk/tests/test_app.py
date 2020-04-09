#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.


import sys
import argparse
import resilient_sdk.app as app


def test_get_main_app_parser():
    # Append to command line arguments, using sys.argv.append()
    sys.argv.append("-v")

    parser = app.get_main_app_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.description == "Python SDK for developing Resilient Apps"
    assert parser.epilog == "For support, please visit ibm.biz/resilientcommunity"

    args = parser.parse_known_args()[0]

    assert args.verbose is True


def test_get_main_app_sub_parser():
    main_parser = app.get_main_app_parser()
    sub_parser = app.get_main_app_sub_parser(main_parser)

    assert sub_parser.dest == "cmd"
    assert sub_parser.container.description == "one of these subcommands must be provided"
    assert sub_parser.container.title == "subcommands"
