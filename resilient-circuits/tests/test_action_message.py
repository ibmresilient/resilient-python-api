#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_circuits.action_message import ActionMessageBase, InboundMessage
from tests import mock_constants


class TestInboundMessage:

    def test_basic_instantiation(self):

        mock_event = InboundMessage(queue=mock_constants.MOCK_QUEUE)
        assert isinstance(mock_event, ActionMessageBase)
        assert isinstance(mock_event, InboundMessage)
        assert mock_event.name == mock_constants.MOCK_QUEUE_NAME

    def test_queue_not_tuple(self):
        with pytest.raises(AssertionError):
            InboundMessage(queue="no queue")
