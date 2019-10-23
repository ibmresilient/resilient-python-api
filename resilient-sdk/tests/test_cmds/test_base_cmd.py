#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

import sys
import pytest
import resilient_sdk.app as app
from resilient_sdk.cmds.base_cmd import BaseCmd


@pytest.fixture
def fx_get_sub_parser():
    """
    Before: Return a main_parser setup with sub_parser added
    After: Nothing
    """
    main_parser = app.get_main_app_parser()
    sub_parser = app.get_main_app_sub_parser(main_parser)
    return sub_parser


def test_no_CMD_NAME(fx_get_sub_parser):

    class MockClass(BaseCmd):
        pass

    with pytest.raises(AssertionError):
        MockClass(fx_get_sub_parser)


def test_no_CMD_HELP(fx_get_sub_parser):

    class MockClass(BaseCmd):
        CMD_NAME = "mock"

    with pytest.raises(AssertionError):
        MockClass(fx_get_sub_parser)


def test_no_setup_method(fx_get_sub_parser):
    class MockClass(BaseCmd):
        CMD_NAME = "mock"
        CMD_HELP = "mock"

    with pytest.raises(NotImplementedError):
        MockClass(fx_get_sub_parser)


def test_get_common_parser(fx_cmd_line_args_codegen_package):
    class MockClass(BaseCmd):
        CMD_NAME = "mock"
        CMD_HELP = "mock"

        def setup(self):
            pass

        def execute_command(self):
            pass

    common_parser = MockClass._get_common_parser()

    assert isinstance(common_parser, list)
    assert len(common_parser) == 1

    args = common_parser[0].parse_known_args()[0]

    assert args.function == ["mock_function_one"]
    assert args.messagedestination == ["fn_main_mock_integration"]
    assert args.rule == ["Mock Manual Rule", "Mock: Auto Rule", "Mock Task Rule", "Mock Script Rule", "Mock Manual Rule Message Destination"]
    assert args.workflow == ["mock_workflow_one", "mock_workflow_two"]
    assert args.field == ["mock_field_number", "mock_field_number", "mock_field_text_area"]
    assert args.artifacttype == ["mock_artifact_2", "mock_artifact_type_one"]
    assert args.datatable == ["mock_data_table"]
    assert args.task == ["mock_custom_task_one", "mock_cusom_task__________two"]
    assert args.script == ["Mock Script One"]
    assert args.exportfile is None
    assert args.output is None
