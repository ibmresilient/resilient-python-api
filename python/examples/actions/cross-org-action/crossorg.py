"""Listen for "escalate cross org" commands on a Resilient Action Message Destination"""

from __future__ import print_function
from __future__ import absolute_import

import co3
import json
import os
import logging
import time
import stomp
import ssl
from stomp_listener import StompListener
from crossorg_argparse import CrossOrgArgumentParser
from crossorg_actions import CrossOrgActions


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
    opts = CrossOrgArgumentParser().parse_args()

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

    # Connect to the destination
    dest_url = "https://{}:{}".format(opts.get("desthost", ""), opts.get("destport", 443))
    dest_resilient_client = co3.SimpleClient(org_name=opts.get("destorg"),
                                             proxies=opts.get("destproxy"),
                                             base_url=dest_url,
                                             verify=opts.get("cafile") or True)
    dest_resilient_client.connect(opts["destemail"], opts["destpassword"])

    # Class instance that will do the work
    worker = CrossOrgActions(opts, resilient_client, dest_resilient_client)

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
