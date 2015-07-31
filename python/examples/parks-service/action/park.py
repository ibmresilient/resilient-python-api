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

"""Listen for search commands on a Resilient Action Message Destination"""

from __future__ import print_function
from __future__ import absolute_import

import co3
import json
import os
import logging
import time
import stomp
import ssl
from park_argparse import ParkArgumentParser
from stomp_listener import StompListener
from park_actions import ParkActions


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_cert(cert, hostname):
    """Utility wrapper for SSL validation on the STOMP connection"""
    try:
        co3.match_hostname(cert, hostname)
    except Exception as exc:
        return (False, str(exc))
    return (True, "Success")


def main():
    """main"""

    # Parse commandline arguments
    parser = ParkArgumentParser()
    opts = parser.parse_args()

    # Create SimpleClient for a REST connection to the Resilient services
    url = "https://{}:{}".format(opts.get("host", ""), opts.get("port", 443))

    resilient_client = co3.SimpleClient(org_name=opts.get("org"),
                                        proxies=opts.get("proxy"),
                                        base_url=url,
                                        verify=opts.get("cafile") or True)
    userinfo = resilient_client.connect(opts["email"], opts["password"])
    logger.debug(json.dumps(userinfo, indent=2))
    if(len(userinfo["orgs"])) > 1 and opts.get("org") is None:
        logger.error("User is a member of multiple organizations; please specify one.")
        exit(1)
    if(len(userinfo["orgs"])) > 1:
        for org in userinfo["orgs"]:
            if org["name"] == opts.get("org"):
                org_id = org["id"]
    else:
        org_id = userinfo["orgs"][0]["id"]


    # Make a ParkActions that will do the work
    worker = ParkActions(opts, resilient_client, opts.get("park"))


    # Set up a STOMP connection to the Resilient action services
    host_port = (opts["host"], opts["stomp_port"])
    conn = stomp.Connection(host_and_ports=[(host_port)], try_loopback_connect=False)

    # Give the STOMP library our TLS/SSL configuration.
    conn.set_ssl(for_hosts=[host_port],
                 ca_certs=opts.get("cafile"),
                 ssl_version=ssl.PROTOCOL_TLSv1,
                 cert_validator=validate_cert)

    # When queued events happen, the worker will handle them
    conn.set_listener('', StompListener(conn, worker.handle_message))
    conn.start()
    conn.connect(login=opts["email"], passcode=opts["password"])

    # Subscribe to the destination.
    conn.subscribe(id='stomp_listener',
                   destination="actions.{}.{}".format(org_id, opts["queue"]),
                   ack='auto')

    try:
        logger.info("\nWaiting for messages.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nBye!")


if __name__ == "__main__":
    main()
