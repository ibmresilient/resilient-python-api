#!/usr/bin/env python
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
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

try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty


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

    def __init__(self, host, port):
        cmd.Cmd.__init__(self)
        self.message_queue = Queue()
        self.response_queue = Queue()
        self.message_id = 0
        self.conn_thread = ConnectionThread(host, port, self.message_queue,
                                            self.print_response)
        signal.signal(signal.SIGINT, self.killed)
        signal.signal(signal.SIGTERM, self.killed)
        self.conn_thread.start()

    def postloop(self):
        self.conn_thread.stop()

    #
    # -------- Test Commands --------
    #
    def do_submit(self, arg):
        """Submit action from specified queue:  submit <destination_queue> <action_json> """
        queue, action_json = self._parse_arg(arg)
        self._submit_action(queue, action_json)
    # end do_submit

    def do_submitfile(self, arg):
        """Submit action stored in a file from specified queue:  submitfile <destination_queue> <file containing action_json> """
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
    parser.add_argument('--host', dest='host', default='localhost',
                        help=("hostname where resilient_circuits program "
                              "is running. Defaults to localhost."))
    parser.add_argument('--port', dest='port', default=8008, type=int,
                        help=("port where resilient_circuits action "
                              "test server is listening. defaults to 8008"))
    args = parser.parse_args()
    ResilientTestProcessor(args.host, args.port).cmdloop()
    
if __name__ == '__main__':
    main()
