#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_circuits.cmds import selftest


def test_error_connecting_to_soar_rest(caplog):
    with pytest.raises(SystemExit) as sys_exit:
        selftest.error_connecting_to_soar("mock_host", status_code=20)

    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == 20


def test_check_soar_rest_connection():
    # TODO
    pass
