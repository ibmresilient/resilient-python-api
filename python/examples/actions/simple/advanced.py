"""Slightly advanced example with Action Module; includes REST API usage."""

from __future__ import print_function

import sys
import stomp
import ssl
import json
import time
import co3
import cafargparse
import logging
from datetime import datetime


class Co3Listener(object):
    """The stomp library will call our listener's on_message when a message is received."""

    def __init__(self, stomp_conn, co3_client):
        self.stomp_conn = stomp_conn
        self.co3_client = co3_client

    def on_error(self, headers, message):
        """Report an error from the message queues"""
        print('received an error {}'.format(message))

    def on_message(self, headers, message):
        """Handle a message"""
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
            incident['description'] = incident['description'] + "\n\nUpdate from Action Module example {}.".format(now)

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


def main():
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

    # Check the org ID that we connected as
    # is the same as the org ID in the action destination
    destination = opts.destination[0]
    destination_parts = destination.split(".")
    if len(destination_parts)==3:
        org_id = destination_parts[1]
        if int(org_id) != co3_client.org_id:
            print("Org {} does not match destination {}".format(co3_client.org_id, destination))
            exit(1)

    # Setup the STOMP stomp_connection.
    stomp_conn = stomp.Connection(host_and_ports=[host_port], try_loopback_connect=False)

    # Configure a listener.
    stomp_conn.set_listener('', Co3Listener(stomp_conn, co3_client))

    # Give the STOMP library our TLS/SSL configuration.
    stomp_conn.set_ssl(for_hosts=[host_port],
                       ca_certs=opts.cafile,
                       ssl_version=ssl.PROTOCOL_TLSv1,
                       cert_validator=validate_cert)

    # Actually connect.
    stomp_conn.start()
    stomp_conn.connect(login=opts.email, passcode=opts.password)

    # Subscribe to the destination.
    stomp_conn.subscribe(id='stomp_listener', destination=opts.destination[0], ack='auto')

    print("Waiting for messages...")

    # The listener gets called asynchronously, so we need to sleep here.
    while 1:
        time.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
