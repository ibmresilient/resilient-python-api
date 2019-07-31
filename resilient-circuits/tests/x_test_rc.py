# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
from __future__ import print_function
import pytest
import doctest
import time
import types
import os
import resilient_circuits
import resilient_circuits.bin
import resilient_circuits.util


class TestRC:
    """Basic API tests"""

    def test_doctest(self):
        """Run doctest on all modules, even if you didn't --doctest-modules"""
        for item in resilient_circuits.__dict__.values():
            if isinstance(item, types.ModuleType):
                if 'resilient-circuits' in os.path.dirname(item.__file__):
                    doctest.testmod(item, verbose=True, raise_on_error=True)

        for item in resilient_circuits.bin.__dict__.values():
            if isinstance(item, types.ModuleType):
                doctest.testmod(item, verbose=True, raise_on_error=True)

        for item in resilient_circuits.util.__dict__.values():
            if isinstance(item, types.ModuleType):
                doctest.testmod(item, verbose=True, raise_on_error=True)
