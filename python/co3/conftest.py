""" pytest configuration for co3 tests """
import argparse

def pytest_addoption(parser):
    parser.addoption("--config-file",
                     help="Resilient Config File",
                     default="",
                     required=False)
    parser.addoption('--co3args',
                     help="Optional Resilient Args",
                     default = "",
                     required=False)
