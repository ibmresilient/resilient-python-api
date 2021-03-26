#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

from resilient_circuits.action_message import ActionMessageBase, InboundMessage
from tests import helpers


class TestInboundMessage:

    def test_basic_instantiation(self):

        mock_event = InboundMessage(queue=helpers.MOCK_QUEUE)
        assert isinstance(mock_event, ActionMessageBase)
        assert isinstance(mock_event, InboundMessage)
        assert mock_event.name == helpers.MOCK_QUEUE_NAME
