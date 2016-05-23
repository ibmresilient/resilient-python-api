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

"""Global accessor for the Resilient REST API"""

import co3
import json
import logging
LOG = logging.getLogger(__name__)
resilient_client = None


def reset_resilient_client():
    """Reset the cached client"""
    global resilient_client
    resilient_client = None


def get_resilient_client(opts):
    """Get a connected instance of SimpleClient for Resilient REST API"""
    global resilient_client
    if resilient_client:
        return resilient_client

    # Create SimpleClient for a REST connection to the Resilient services
    url = "https://{0}:{1}".format(opts.get("host", ""), opts.get("port", 443))
    resilient_client = co3.SimpleClient(org_name=opts.get("org"),
                                        proxies=opts.get("proxy"),
                                        base_url=url,
                                        verify=opts.get("cafile") or True)

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

    return resilient_client
