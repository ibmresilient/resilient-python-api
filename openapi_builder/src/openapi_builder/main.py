# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order
from argparse import ArgumentParser
from pathlib import Path
import sys

# uncomment for src debugging
# from components.openapi_builder import OpenAPIBuilder
# from components.constants import DEFAULT_OPENAPI_VERSION
from openapi_builder.components.openapi_builder import OpenAPIBuilder
from openapi_builder.components.constants import DEFAULT_OPENAPI_VERSION
import pkg_resources  # part of setuptools

version = pkg_resources.require("OpenAPIBuilder")[0].version


def parse_args(*args):
    """parse arguments to this app such as:
        - existing openapi spec file
        - version of openapi spec to use

    :return: parsed arguments
    :rtype: arg_parser.Namespace
    """
    arg_parser = ArgumentParser()
    arg_parser.add_argument("file",
                        nargs='?',
                        help="Optional existing OpenAPI spec file to enhance (json or yaml format supported)")
    arg_parser.add_argument("-v", "--version",
                        default=DEFAULT_OPENAPI_VERSION,
                        help="Document version of OpenAPI specification to use. Default 3.0.0",
                        required=False)
    arg_parser.add_argument("-s", "--soar",
                        action='store_true',
                        default=False,
                        help="Added prompts for use with IBM's SOAR low-code connectors",
                        required=False)
    arg_parser.add_argument("-t", "--terse",
                        action='store_true',
                        default=False,
                        help="Reduces explanation of prompts",
                        required=False)

    return arg_parser.parse_args(args)

# S T A R T
def main():
    """ parse the input parameters and kick off the tool """
    args = parse_args(*sys.argv[1:])
    openapi_builder = OpenAPIBuilder(args)
    openapi_builder.start(version)

if __name__ == "__main__":
    file = Path(__file__).resolve()
    main()
