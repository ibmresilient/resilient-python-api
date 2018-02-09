# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
""" pytest configuration for co3 tests """
import argparse
import pytest


def pytest_addoption(parser):
    parser.addoption("--config-file",
                     help="Resilient Config File",
                     default="",
                     required=False)
    parser.addoption('--co3args',
                     help="Optional Resilient Args",
                     default="",
                     required=False)


@pytest.fixture(scope="session")
def co3_args(request):
    print("co3_args fixture")
    import shlex
    import resilient

    config_file = request.config.getoption("--config-file")
    co3args = request.config.getoption("--co3args")
    co3args = shlex.split(co3args)

    args = resilient.ArgumentParser(config_file=config_file).parse_args(args=co3args)
    return args
