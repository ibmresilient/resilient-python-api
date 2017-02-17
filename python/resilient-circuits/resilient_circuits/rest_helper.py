#!/usr/bin/env python

"""Global accessor for the Resilient REST API"""

import co3
import json
import logging
import requests
LOG = logging.getLogger(__name__)
resilient_client = None
connection_opts = None


def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None


def get_resilient_client(opts):
    """Get a connected instance of SimpleClient for Resilient REST API"""
    global resilient_client
    global connection_opts

    new_opts = (opts.get("cafile"),
                opts.get("org"),
                opts.get("host"),
                opts.get("port"),
                opts.get("proxy"),
                opts.get("email"))
    if new_opts != connection_opts:
        resilient_client = None
        connection_opts = new_opts
    if resilient_client:
        return resilient_client

    # Allow explicit setting "do not verify certificates"
    verify = opts.get("cafile")
    if verify == "false":
        LOG.warn("Unverified HTTPS requests (cafile=false).")
        requests.packages.urllib3.disable_warnings()  # otherwise things get very noisy
        verify = False

    # Create SimpleClient for a REST connection to the Resilient services
    url = "https://{0}:{1}".format(opts.get("host", ""), opts.get("port", 443))
    resilient_client = co3.SimpleClient(org_name=opts.get("org"),
                                        proxies=opts.get("proxy"),
                                        base_url=url,
                                        verify=verify)

    userinfo = resilient_client.connect(opts["email"], opts["password"])

    # Validate the org, and store org_id in the opts dictionary
    LOG.debug(json.dumps(userinfo, indent=2))
    if(len(userinfo["orgs"])) > 1 and opts.get("org") is None:
        raise Exception("User is a member of multiple organizations; please specify one.")
    if(len(userinfo["orgs"])) > 1:
        for org in userinfo["orgs"]:
            if org["name"] == opts.get("org"):
                opts["org_id"] = org["id"]
    else:
        opts["org_id"] = userinfo["orgs"][0]["id"]

    # Check if action module is enabled and store to opts dictionary
    org_data = resilient_client.get('')
    resilient_client.actions_enabled = org_data["actions_framework_enabled"]


    return resilient_client
