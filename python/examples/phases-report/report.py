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

"""Produce reports from incident history"""

from __future__ import print_function
from __future__ import absolute_import

import co3
import json
import os
import logging
import time
import csv
from report_argparse import ReportArgumentParser
from datetime import datetime
from calendar import timegm

# Report times in hours, not milliseconds
FACTOR = (60*60*1000)

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_json_time(dt):
    """Epoch timestamp from datetime"""
    return timegm(dt.utctimetuple()) * 1000

def all_incidents(resilient_client, created_since_date):
    """Yield all the incidents"""
    # Query is more efficient than just reading the full description of every incident.
    # But caution: it only returns the partial incident DTO.
    conditions = [{"field_name": "inc_training", "method": "equals", "value": False}]
    if created_since_date:
        conditions.append({"field_name": "create_date", "method": "gt", "value":get_json_time(created_since_date)})
    query = {"filters": [{"conditions": conditions}]}
    logger.debug(json.dumps(query, indent=2))
    incidents = resilient_client.post("/incidents/query", query)
    for incident in incidents:
        yield incident

def query_newsfeed(resilient_client, incident_id, query):
    """Yield newsfeed items that match a query"""
    # For these queries, /newsfeed is more efficient than /history.
    query_string = "&".join(["{}={}".format(qq, query[qq]) for qq in query.keys()])
    url = "/incidents/{}/newsfeed?{}".format(incident_id, query_string)
    items = resilient_client.get(url)
    logger.debug(json.dumps(items, indent=2))
    for item in items:
        yield item

def phases_report(opts, resilient_client):
    """Produce the report of time-on-phase for every incident"""
    # The list of all phases
    phase_data = resilient_client.get("/phases")
    phases = [phase["name"] for phase in phase_data["entities"]]

    with open("phases.csv", 'w') as temp:
        # Two initial columns: incident id, and status
        writer = csv.DictWriter(temp, fieldnames=["#", "Active?"] + phases, dialect='excel')
        writer.writeheader()

        for incident in all_incidents(resilient_client, opts.get("since")):
            logger.info("Incident %s", incident["id"])
            last_ts = incident["create_date"]
            now_ts = int(time.time() * 1000)
            end_ts = now_ts
            if incident["plan_status"] == "C":
                # incident is closed, find its end-date
                end_ts = resilient_client.get("/incidents/{}".format(incident["id"]))["end_date"]

            # Figure out time on phase from changes
            items = query_newsfeed(resilient_client, incident["id"], {"entry_type": "PHASE_CHANGE"})
            current_phase = None
            phase_duration = {"#": incident["id"], "Active?": incident["plan_status"]}
            for item in sorted(items, key=lambda x: x["timestamp"]):
                timestamp = item["timestamp"]
                previous_phase = item["before"]
                current_phase = item["after"]
                duration = phase_duration.get(previous_phase, 0)
                phase_duration[previous_phase] = duration + float(timestamp - last_ts)/FACTOR
                last_ts = timestamp

            # Add the time on "current phase"
            duration = phase_duration.get(current_phase, 0)
            if current_phase:
                phase_duration[current_phase] = duration + float(end_ts - last_ts)/FACTOR
                writer.writerow(phase_duration)

            # print(json.dumps(phase_duration))


def main():
    """main"""

    # Parse commandline arguments
    parser = ReportArgumentParser()
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

    # Do the reports
    phases_report(opts, resilient_client)


if __name__ == "__main__":
    main()
