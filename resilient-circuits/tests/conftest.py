#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
Shared pytest fixtures

Note:
    -   Code after the 'yield' statement in a fixture
        is ran after the test (or scope i.e. test session) has complete
    -   fx_ prefixes a 'fixture'
    -   Put fixture logic in separate 'private' function so we
        can share logic between fixtures
    -   Fixture must have BEFORE and AFTER docstring
"""

import copy
import sys
import pytest


@pytest.fixture
def fx_clear_cmd_line_args():
    """
    Before: Clear command line arguments
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    sys.argv = [sys.argv[0]]

    yield

    sys.argv = original_cmd_line
