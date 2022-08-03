#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_circuits.action_message import ActionMessageBase, InboundMessage, FunctionResult
from tests import mock_constants


class TestFunctionResult:

    def test_basic_instantiation(self):

        mock_results = {"content": u"unicode: ล ฦ ว"}
        mock_fn_name = "mock_fn_name"

        result = FunctionResult(mock_results, name=mock_fn_name)

        assert result.value == mock_results
        assert result.name == mock_fn_name
        assert result.reason is None
        assert result.success is True
        assert result.custom_results is False

    def test_custom_result_instantiation(self):

        mock_results = {"content": u"unicode: ล ฦ ว"}
        mock_fn_name = "mock_fn_name"

        result = FunctionResult(mock_results, name=mock_fn_name, success=False, reason="Failure", custom_results=True)

        assert result.value == mock_results
        assert result.name == mock_fn_name
        assert result.reason == "Failure"
        assert result.success is False
        assert result.custom_results is True

    def test_results_not_dict(self, caplog):

        error_msg = "FunctionResult must be a dictionary"
        FunctionResult("")
        assert error_msg in caplog.text


class TestInboundMessage:

    def test_basic_instantiation(self):

        mock_event = InboundMessage(queue=mock_constants.MOCK_QUEUE)
        assert isinstance(mock_event, ActionMessageBase)
        assert isinstance(mock_event, InboundMessage)
        assert mock_event.name == mock_constants.MOCK_QUEUE_NAME

    def test_queue_not_tuple(self):
        with pytest.raises(AssertionError):
            InboundMessage(queue="no queue")
