#!/usr/bin/env python

# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import os
import stomp
import ssl
import json
import time
import co3
import cafargparse
import logging
from datetime import datetime

logging.basicConfig()

# The stomp library will call our listener's on_message when a message is received.
class Co3Listener(object):
  def __init__(self, stomp_conn, co3_client):
    self.stomp_conn = stomp_conn
    self.co3_client = co3_client

  def on_error(self, headers, message):
    print('received an error {}'.format(message))

  def on_message(self, headers, message):
    if message == "SHUTDOWN":
      print("Shutting down")
      self.stomp_conn.disconnect()
      sys.exit(0)

    # Get the relevant headers.
    reply_to = headers['reply-to']
    correlation_id = headers['correlation-id']
    context = headers['Co3ContextToken']

    # Convert from a JSON string to a Python dict object.
    json_obj = json.loads(message)

    # Get the incident ID
    inc_id = json_obj['incident']['id']

    # Do a GET, apply our change, then do a PUT.
    inc_url = '/incidents/{}'.format(inc_id)

    # Apply the changes.  For this example, just update the description with the current time.
    now = str(datetime.now())

    def apply_change(incident):
        incident['description'] = incident['description'] + "\n\nUpdate from CAF example {}.".format(now)

    # get_put will do a GET on the URL, call apply_change the do a PUT on the resulting object.
    # If the operation fails with a 409 (conflict) error, the operation is retried.
    #
    # Note that we specify the context token here.
    self.co3_client.get_put(inc_url, apply_change, context)

    print("Updated description of incident {}".format(inc_id))

    # Send the reply back to the Resilient server indicating that everything was OK.
    reply_message = '{"message_type": 0, "message": "Processing complete", "complete": true}'

    self.stomp_conn.send(reply_to, reply_message, headers={'correlation-id': correlation_id})

def validate_cert(cert, hostname):
    try:
        co3.match_hostname(cert, hostname)
    except Exception as ce:
        return (False, str(ce))

    return (True, "Success")

def main(argv):
    # Parse out the command line options.
    parser = cafargparse.CafArgumentParser()

    opts = parser.parse_args()

    host_port = (opts.shost, opts.sport)

    # Note that we use the same email and password to connect to the Resilient REST API as we
    # do to connect to the Resilient STOMP server.

    # Create SimpleClient and connect
    verify = True
    if opts.cafile:
        verify = opts.cafile

    base_url = "https://{}:{}".format(opts.host, opts.port)

    co3_client = co3.SimpleClient(org_name=opts.org, proxies=opts.proxy, base_url=base_url, verify=verify)

    co3_client.connect(opts.email, opts.password)

    # Setup the STOMP stomp_connection.
    stomp_conn = stomp.Connection(host_and_ports = [host_port], try_loopback_connect=False)

    # Configure a listener.
    stomp_conn.set_listener('', Co3Listener(stomp_conn, co3_client))

    # Give the STOMP library our TLS/SSL configuration.
    stomp_conn.set_ssl(for_hosts=[host_port], ca_certs = opts.cafile, ssl_version = ssl.PROTOCOL_TLSv1, cert_validator = validate_cert)

    # Actually connect.
    stomp_conn.start()
    stomp_conn.connect(login = opts.email, passcode = opts.password)

    # Subscribe to the destination.
    stomp_conn.subscribe(id = 'stomp_listener', destination = opts.destination[0], ack = 'auto')

    print("Waiting for messages...")

    # The listener gets called asynchronously, so we need to sleep here.
    while 1:
        time.sleep(10)

if __name__ == "__main__":
   main(sys.argv[1:])
