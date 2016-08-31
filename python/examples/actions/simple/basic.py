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

"""Basic example with Action Module; just subscribes to messages."""

from __future__ import print_function

import sys
import ssl
import json
import time
import logging
import stomp
import co3
import cafargparse
from requests.utils import DEFAULT_CA_BUNDLE_PATH


class Co3Listener(object):
    """The stomp library will call our listener's on_message when a message is received."""

    def __init__(self, conn):
        self.conn = conn

    def on_error(self, headers, message):
        """Report an error from the message queues"""
        print('received an error {}'.format(message))

    def on_message(self, headers, message):
        """Handle a message"""
        if message == "SHUTDOWN":
            print("Shutting down")
            self.conn.disconnect()
            sys.exit(0)

        # Convert from a JSON string to a Python dict object.
        json_obj = json.loads(message)

        sev_id = json_obj['incident']['severity_code']

        # The metadata for the severity field is stored at:
        #
        #  json_obj.type_info.incident.fields.severity_code.values.ID
        sev_field = json_obj['type_info']['incident']['fields']['severity_code']

        sev_value = sev_field['values'].get(str(sev_id))
        if sev_value:
            text = sev_value['label']
        else:
            text = str(sev_id)

        # Pull out incident object.
        inc = json_obj['incident']

        print('received action for incident {}:  name={}; sev={}'.format(inc['id'], inc['name'], text))

        # Get the relevant headers.
        reply_to = headers['reply-to']
        correlation_id = headers['correlation-id']
        context = headers['Co3ContextToken']

        # send the reply back to the Resilient server indicating that everything was OK.
        reply_message = '{"message_type": 0, "message": "Processing complete", "complete": true}'

        self.conn.send(reply_to, reply_message, headers={'correlation-id': correlation_id})


def validate_cert(cert, hostname):
    try:
        co3.match_hostname(cert, hostname)
    except Exception as ce:
        return (False, str(ce))

    return (True, "Success")


def main():
    # Parse out the command line options.
    parser = cafargparse.CafArgumentParser()
    opts = parser.parse_args()

    host_port = (opts.shost, opts.sport)

    # Setup the STOMP connection.
    conn = stomp.Connection(host_and_ports=[host_port], try_loopback_connect=False)

    # Configure a listener.
    conn.set_listener('', Co3Listener(conn))

    # Give the STOMP library our TLS/SSL configuration.
    validator_function = validate_cert
    cafile = opts.cafile
    if cafile == "false":
        # Explicitly disable TLS certificate validation, if you need to
        cafile = None
        validator_function = None
        print("TLS without certificate validation: Insecure! (cafile=false)")
    elif cafile is None:
        # Since the REST API (co3 library) uses 'requests', let's use its default certificate bundle
        # instead of the certificates from ssl.get_default_verify_paths().cafile
        cafile = DEFAULT_CA_BUNDLE_PATH
        print("TLS validation with default certificate file: {0}".format(cafile))
    else:
        print("TLS validation with certificate file: {0}".format(cafile))
    conn.set_ssl(for_hosts=[host_port],
                 ca_certs=cafile,
                 ssl_version=ssl.PROTOCOL_TLSv1,
                 cert_validator=validator_function)

    conn.start()

    # Actually connect.
    conn.connect(login=opts.email, passcode=opts.password)

    # Subscribe to the destination.
    conn.subscribe(id='stomp_listener', destination=opts.destination[0], ack='auto')

    print("Waiting for messages...")

    # The listener gets called asynchronously, so we need to sleep here.
    while 1:
        time.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
