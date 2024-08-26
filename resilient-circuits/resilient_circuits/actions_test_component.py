# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Test Server component for injecting test Action Module messages"""

from __future__ import print_function
import logging
import time
import json
import struct
import uuid
from circuits import Component, Event, handler
from circuits.net.sockets import TCPServer
from circuits.net.events import write
from resilient_circuits.action_message import ActionMessage, FunctionMessage, InboundMessage, LowCodeMessage
from resilient_circuits import constants, helpers


DEFAULT_TEST_HOST = "localhost"
DEFAULT_TEST_PORT = 8008
DEFAULT_WORKFLOW_INSTANCE_ID = 999

LOG = logging.getLogger(__name__)


class SubmitTestAction(Event):
    """ Circuits event to insert a test Action Message """
    def __init__(self, queue, msg_id, message):
        if not all((queue, msg_id, message)):
            raise ValueError("queue, msg_id, and message are required")
        super(SubmitTestAction, self).__init__(queue=queue, msg_id=msg_id, message=message)


class SubmitTestFunction(Event):
    """ Circuits event to insert a test Function Message """
    def __init__(self, function_name, function_params):
        if not function_name or not isinstance(function_params, dict):
            raise ValueError("function_name and function_params are required")
        msg_id = str(uuid.uuid4())
        super(SubmitTestFunction, self).__init__(queue="example", msg_id=msg_id, message={
            "function": {
                "name": function_name
            },
            "inputs": function_params,
            "workflow_instance": {
                "workflow_instance_id": DEFAULT_WORKFLOW_INSTANCE_ID
            }
        })


class SubmitTestInboundApp(Event):

    def __init__(self, queue_name, action, content, message=None):

        msg_id = str(uuid.uuid4())

        if not message:
            message = {
                "origin": {
                    "source": "mock_source",
                    "name": "mock.domain.com",
                    "id": "",
                    "version": "1.1.1"
                },
                "schema_version": "1.0",
                "content_type": "offense",
                "content_date": "2020-11-15T00:00:00+0600",
                "content_schema_version": "1.0",
                "action": action,
                "content": content
            }

        super(SubmitTestInboundApp, self).__init__(queue_name=queue_name, msg_id=msg_id, message=message)

class SubmitTestLowCodeApp(Event):

    def __init__(self, queue_name, message=None):

        msg_id = str(uuid.uuid4())

        # TODO: mock out values
        if not message:
            message = {
                "request_originator": {
                    "request_uuid": str(uuid.uuid4()),
                    "correlation_id": "invid:100",
                    "function_programmatic_name": "createUsersWithListInput",
                    "org_id":201,
                    "object_id":2095,
                    "object_type":"incident",
                    "parent_object_id":2095,
                    "playbook_id":3,
                    "playbook_instance_id":100
                },
                "request_payload": {
                    "server_url":"https://petstore.swagger.io/v2/user/createWithList",
                    "method":"POST",
                    "request_body": [ {
                        "id":12,
                        "email":"john3@email.com",
                        "phone":"12345",
                        "lastName":"Doe",
                        "password":"12345",
                        "username":"theUser",
                        "firstName":"James",
                        "userStatus":1
                    } ] ,
                    "request_content_type":"application/json",
                    "response_content_type":"application/json",
                    "custom_params":{
                        "secureContext":"true"
                    },
                    "security":{
                        "scheme":"APIKEY",
                        "api_key_param_name":"api_key",
                        "api_key":"*****",
                        "api_key_in":"HEADER",
                        "generate_bearer_token":False
                    }
                },
                "response_acknowledgment":{
                    "ack_url":"http://localhost:8080/rest/orgs/201/serverless/ack",
                    "ack_security":{
                        "scheme":"BASIC",
                        "api_key":"*****",
                        "api_key_secret":"*****",
                        "generate_bearer_token":False
                    }
                }
            }

        super(SubmitTestLowCodeApp, self).__init__(queue_name=queue_name, msg_id=msg_id, message=message)


class ResilientTestActions(Component):
    """ Mock the stomp connection for testing"""

    def __init__(self, org_id, host=DEFAULT_TEST_HOST, port=DEFAULT_TEST_PORT):
        super(ResilientTestActions, self).__init__()
        self.org_id = org_id
        bind = (host, port)
        LOG.debug("Binding test server to %s:%d", host, port)
        TCPServer(bind).register(self)
        self.messages_in_progress = {}
        self.actions_sent = {}

    def usage(self):
        return "Submit actions with format: <queue> <message json>"

    @handler("SubmitTestAction", "SubmitTestFunction")
    def _submit_message(self, event, queue, msg_id, message, channel="*"):
        """ Create and fire an ActionMessage """
        try:
            message_id = "ID:resilient-54199-{val}-6:2:12:1:1".format(val=msg_id)
            reply_to = "/queue/acks.{org}.{queue}".format(org=self.org_id,
                                                          queue=queue)
            destination = "/queue/actions.{org}.{queue}".format(org=self.org_id,
                                                                queue=queue)
            headers = {"reply-to": reply_to,
                       "expires": "0",
                       "timestamp": str(int(time.time()) * 1000),
                       "destination": destination,
                       "correlation-id": "invid:390",
                       "persistent": "True",
                       "priority": "4",
                       "Co3MessagePayload": "ActionDataDTO",
                       "Co3ContentType": "application/json",
                       "message-id": message_id,
                       "Co3ContextToken": "dummy",
                       "subscription": "stomp-{queue}".format(queue=queue)}
            try:
                sock = self.actions_sent.get(msg_id)
                if not isinstance(message, dict):
                    message = json.loads(message)
                    assert(isinstance(message, dict))
            except Exception as e:
                LOG.exception("Bad Message<action %d>: %s", msg_id, message)
                if sock:
                    msg = "Bad Message<action %d>! %s" % (msg_id, str(e))
                    self.fire_message(sock, msg)
                return

            if message.get("function"):
                channel = "functions." + message["function"]["name"]
                action_event = FunctionMessage(source=self.parent,
                                               headers=headers,
                                               message=message,
                                               test=True,
                                               test_msg_id=msg_id)
            else:
                channel = "actions." + queue
                action_event = ActionMessage(source=self.parent,
                                             headers=headers,
                                             message=message,
                                             test=True,
                                             test_msg_id=msg_id)
            action_event.parent = event
            self.fire(action_event, channel)
            if sock:
                self.fire_message(sock, "Action Submitted<action %d>" % msg_id)
        except Exception as e:
            LOG.exception("Action Failed<action %d>", msg_id)
            if sock:
                msg = "Action Failed<action %d>: %s" % (msg_id,
                                                        str(e))
                self.fire_message(sock, msg)

    @handler("SubmitTestInboundApp")
    def _submit_inbound_message(self, event, queue_name, msg_id, message, channel="*"):
        try:
            message_id = "ID:resilient-54199-{msg_id}-6:2:12:1:1".format(msg_id=msg_id)
            subscription = "{0}.{1}.{2}".format(constants.INBOUND_MSG_DEST_PREFIX, self.org_id, queue_name)
            destination = "/queue/{0}".format(subscription)
            queue = helpers.get_queue(destination)

            headers = {
                "timestamp": str(int(time.time()) * 1000),
                "persistent": "True",
                "message-id": message_id,
                "priority": "4",
                "subscription": subscription,
                "destination": destination,
                "expires": "0"
            }

            try:

                if not isinstance(message, dict):
                    message = json.loads(message)
                    assert(isinstance(message, dict))

            except Exception as e:
                LOG.exception("Bad InboundMessage <message_id: %s>: %s", msg_id, message)
                raise e

            if queue and queue[0] == constants.INBOUND_MSG_DEST_PREFIX:
                channel = u"{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, queue_name)
                action_event = InboundMessage(source=self.parent,
                                              queue=queue,
                                              headers=headers,
                                              message=message,
                                              test=True,
                                              test_msg_id=msg_id)

            action_event.parent = event
            self.fire(action_event, channel)

        except Exception as e:
            LOG.exception("Failed to SubmitTestInboundApp <message_id: %s>", msg_id)
            raise e
    
    @handler("SubmitTestLowCodeApp")
    def _submit_low_code_message(self, event, queue_name, msg_id, message, channel="*"):
        try:
            message_id = "ID:resilient-54199-{msg_id}-6:2:12:1:1".format(msg_id=msg_id)
            # TODO: might change depending on queue name
            subscription = "{0}.{1}.{2}".format("actions", self.org_id, queue_name)
            destination = "/queue/{0}".format(subscription)
            queue = helpers.get_queue(destination)
            reply_to = "/queue/acks.{org}.{queue}".format(org=self.org_id,
                                                          queue=queue)

            headers = {"reply-to": reply_to,
                        "expires": "0",
                        "timestamp": str(int(time.time()) * 1000),
                        "destination": destination,
                        "correlation-id": "invid:390",
                        "persistent": "True",
                        "priority": "4",
                        "Co3MessagePayload": "ActionDataDTO",
                        "Co3ContentType": "application/json",
                        "message-id": message_id,
                        "Co3ContextToken": "dummy",
                        "subscription": "stomp-{queue}".format(queue=queue)}
            
            try:

                if not isinstance(message, dict):
                    message = json.loads(message)
                    assert(isinstance(message, dict))

            except Exception as e:
                LOG.exception("Bad LowCodeMessage <message_id: %s>: %s", msg_id, message)
                raise e

            channel = constants.LOW_CODE_MSG_DEST_PREFIX # fire all low_code messages on the 'low_code' channel since they are all the same, no matter the queue they come from
            action_event = LowCodeMessage(source=self,
                                    queue_name=queue_name,
                                    headers=headers,
                                    message=message)

            action_event.parent = event
            self.fire(action_event, channel)

        except Exception as e:
            LOG.exception("Failed to SubmitTestLowCodeApp <message_id: %s>", msg_id)
            raise e

    @handler("read")
    def process_data(self, sock, data):
        """ Process data received from TCP stream """
        msg_id = -1  # default
        try:
            data_as_bytes = bytearray(data)
            if sock not in self.messages_in_progress:
                # New message, parse size out
                msg_size = struct.unpack('>I', data_as_bytes[:4])[0]
                partial_msg = data_as_bytes[4:msg_size + 4]
            else:
                # Retrieve what we had so far
                msg_size, partial_msg = self.messages_in_progress.pop(sock)
                partial_msg = partial_msg + data_as_bytes

            if len(partial_msg) < msg_size:
                # Store what we have so far and wait for more
                self.messages_in_progress[sock] = msg_size, partial_msg
                return
            else:
                # Complete message, parse out msg_id, queue, and msg
                msg_id = struct.unpack('>I', partial_msg[:4])[0]
                data = partial_msg[4:msg_size]
                remainder = partial_msg[msg_size:]
                data = data.strip().decode('utf-8')
                if ' ' not in data or len(data) < 2:
                    # Bad Command
                    msg = ("<action %d>: " % msg_id) + self.usage()
                    self.fire_message(sock, msg)
                else:
                    queue, message = data.split(' ', 1)
                    self.actions_sent[msg_id] = sock
                    self.fire(SubmitTestAction(queue, msg_id, message))

                if remainder:
                    # Process remainder
                    self.process_data(sock, remainder)
        except Exception as e:
            LOG.exception("Action Failed<action %d>", msg_id)
            msg = "Action Failed<action %d>: %s" % (msg_id, str(e))
            self.fire_message(sock, msg)

    def connect(self, sock, host, port):
        """Triggered for new connecting TCP clients"""
        pass

    def test_response(self, msg_id, message):
        """ If action orginated from test client, send response"""
        LOG.debug("Received message for test client")
        sock = self.actions_sent.get(msg_id)
        if sock:
            msg = "RESPONSE<action %d>: %s" % (msg_id, message)
            self.fire_message(sock, msg)

    def done(self, event):
        """Handler when done"""
        status = yield self.wait(event)
        status = status.value
        sock = self.actions_sent.get(event.test_msg_id)
        if isinstance(status, Exception):
            msg = "Action Failed<action %d>: %s" % (event.test_msg_id,
                                                    str(Exception))
            self.fire_message(sock, msg)
            raise status
        else:
            status = status + "\n"
            msg = "Action Completed<action %d>: %s" % (event.test_msg_id,
                                                       status)
            self.fire_message(sock, msg)

    def fire_message(self, sock, message):
        """ Prefix message with length before firing"""
        message = message.encode()
        message = struct.pack('>I', len(message)) + message
        LOG.debug("Firing Message: %s", message)
        self.fire(write(sock, message))
