#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.
from __future__ import print_function

"""Resilient Circuits Action Test Tool"""
#
# Usage:
#  $ res-action-test
#

import cmd
import time
import threading
import socket
import select
import sys
import struct
import argparse
import signal
import json
import shlex
import resilient
from resilient_circuits.app import AppArgumentParser
from resilient_circuits.actions_test_component import DEFAULT_TEST_HOST, DEFAULT_TEST_PORT

try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty


def get_input(datatype, prompt, value):
    if value is None:
        if sys.version_info[0] >= 3:
            value = input(prompt)
        else:
            value = raw_input(prompt)
            value = value.decode(sys.stdin.encoding)
    else:
        print("{} {}".format(prompt, value))
    if value == "":
        return None
    if datatype == "number":
        value = int(value)
    elif datatype in ["datepicker", "datetimepicker"]:
        value = int(value)
    elif datatype == "boolean":
        value = value.lower()[0:1] in ["y", "t", "1"]
    elif datatype == "textarea":
        value = {"type": "text", "content": value}
    elif datatype == "select":
        value = {"id": 123, "name": value}
    elif datatype == "multiselect":
        value = [{"id": 123, "name": value}]
    return value


class ConnectionThread(threading.Thread):
    """Thread class managing the TCP connection"""

    def __init__(self, host, port, message_queue, response_callback):
        super(ConnectionThread, self).__init__()
        self._stop_event = threading.Event()
        self.message_queue = message_queue
        self.response_callback = response_callback
        self.host = host
        self.port = port

        self.connect()

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)
        self.client.connect(server_address)

    def reconnect(self):
        self.response_callback(("Connection to Test Server has died.  "
                                "Trying to reconnect..."))
        self.client.close()
        while not self.stopped():
            try:
                self.connect()
                self.response_callback("Connection Restored.")
                return
            except:
                time.sleep(3)

    def run(self):
        while not self.stopped():
            readables, writables, errorables = select.select([self.client],
                                                             [], [self.client],
                                                             1)
            if errorables:
                self.reconnect()
                continue
            if readables:
                msg_len = self.client.recv(4)
                if not msg_len:
                    self.reconnect()
                    continue
                msg_len = struct.unpack('>I', msg_len)[0]
                data = self.client.recv(msg_len).decode()
                self.response_callback(data)
            try:
                msg, msg_id = self.message_queue.get_nowait()
                message = self.format_message(msg, msg_id)
                self.client.send(message)
            except Empty:
                pass

        self.response_callback("Closing connection")
        self.client.close()

    def format_message(self, message, message_id):
        """ Prefix message with length and id and append newline """
        message = self.as_bytes(message + "\n")
        message = struct.pack('>I', message_id) + message
        message = struct.pack('>I', len(message)) + message

        return message

    def as_bytes(self, data):
        return data.encode()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()


class ResilientTestProcessor(cmd.Cmd):
    """Resilient Circuits Test Tool Command Processor"""
    intro = ("Welcome to the Resilient Circuits Action Test Tool. "
             "Type help or ? to list commands.\n")
    prompt = "(restest) "

    def __init__(self, host=DEFAULT_TEST_HOST, port=DEFAULT_TEST_PORT):
        cmd.Cmd.__init__(self)
        self.message_queue = Queue()
        self.response_queue = Queue()
        self.message_id = 0
        try:
            self.conn_thread = ConnectionThread(host, port, self.message_queue,
                                            self.print_response)
        except socket.error:
            print("ERROR: Unable to connect.\n"
                  "The test client requires resilient-circuits already running, with the '--test-actions' option.\n")
            raise
        signal.signal(signal.SIGINT, self.killed)
        signal.signal(signal.SIGTERM, self.killed)
        self.conn_thread.start()

    def postloop(self):
        self.conn_thread.stop()
        self.conn_thread.join()
        print("")

    #
    # -------- Test Commands --------
    #
    def do_submit(self, arg):
        """Submit action from specified queue:  submit <destination_queue> <action_json> """
        queue, action_json = self._parse_arg(arg)
        self._submit_action(queue, action_json)
    # end do_submit

    def do_submitfile(self, arg):
        """Submit action stored in a file from specified queue:
           submitfile <destination_queue> <file containing action_json>
        """
        queue, filename = self._parse_arg(arg)
        try:
            with open(filename) as action_file:
                action_json = action_file.read()
                self._submit_action(queue, action_json)
        except Exception as e:
            print(e)
    # end do_submitfile

    def do_runlist(self, arg):
        """Run a list of commands from a file:  runlist <filename>"""
        if not arg:
            print("runlist command requires a filename")
        try:
            with open(arg) as f:
                self.cmdqueue.extend(f.read().splitlines())
        except Exception as e:
            print("Bad command list file: %s" % str(e))
    # end do_runlist

    def do_quit(self, *args):
        """Quit the Test Tool and exit:  quit"""
        print(("You are exiting the Resilient Circuits "
               "Action Test Tool.  Goodbye.\n"""))
        self.conn_thread.stop()
        return True
    # end do_quit

    def do_EOF(self, *args):
        """ Ctrl+D """
        return self.do_quit()

    def do_function(self, arg):
        """Execute a function"""
        if not arg:
            print("function command requires a function-name")
            return

        parser = AppArgumentParser(config_file=resilient.get_config_file())
        (opts, more) = parser.parse_known_args()
        client = resilient.get_client(opts)

        args = iter(shlex.split(arg))
        try:
            function_name = next(args)
            function_def = client.get("/functions/{}?handle_format=names".format(function_name))
            param_defs = dict({fld["uuid"]: fld for fld in client.get("/types/__function/fields?handle_format=names")})
            function_params = {}
            for param in function_def["view_items"]:
                param_uuid = param["content"]
                param_def = param_defs[param_uuid]
                prompt = "{} ({}, {}): ".format(param_def["name"], param_def["input_type"], param_def["tooltip"])
                try:
                    arg = next(args)
                except StopIteration:
                    arg = None
                function_params[param_def["name"]] = get_input(param_def["input_type"], prompt, arg)

            action_message = {
                "function": {
                    "name": function_name
                },
                "inputs": function_params
            }
            message = json.dumps(action_message, indent=2)
            print(message)
            self._submit_action("function", message)
        except Exception as e:
            print(e)
    # end do_function

    def killed(self, *args):
        """ Handle kill signal """
        self.do_quit()
        self.conn_thread.join()
        raise SystemExit(0)

    # -------- Helping Methods --------
    def print_response(self, data):
        """ print a Test Server response """
        print("\n" + data)
        print(self.prompt, end="")
        sys.stdout.flush()

    def _submit_action(self, queue, action_json):
        """ Send command out over tcp connection """
        if not action_json:
            print("Action required\n")
            return
        self.message_id = self.message_id + 1
        self.message_queue.put((queue + ' ' + action_json, self.message_id))
    # end submit_action

    def _parse_arg(self, arg):
        """ Parse command arguments """
        two_parts = arg.split(' ', 1)
        if len(two_parts) != 2:
            print("Invalid command. Type help or ? to list commands.\n")
            return None, None

        return two_parts
    # end parse_arg


def main():
    description = 'Resilient Circuits Action Test Tool'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--host', dest='host', default=DEFAULT_TEST_HOST,
                        help=("hostname where resilient_circuits program "
                              "is running. Defaults to localhost."))
    parser.add_argument('--port', dest='port', type=int, default=DEFAULT_TEST_PORT,
                        help=("port where resilient_circuits action "
                              "test server is listening. defaults to 8008"))
    args = parser.parse_args()
    ResilientTestProcessor(host=args.host, port=args.port).cmdloop()


if __name__ == '__main__':
    main()
