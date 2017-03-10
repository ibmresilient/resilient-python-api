#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Produce reports from incident history"""

from __future__ import print_function
from __future__ import absolute_import

import co3 as resilient
import os
import json
import logging
import time
import csv
import argparse
from datetime import datetime
from calendar import timegm


# The config file location should usually be set in the environment
APP_CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "report.config")

# Report times in hours, not milliseconds
FACTOR = (60 * 60 * 1000)

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportOpts(dict):
    """A dictionary of the commandline options"""
    def __init__(self, config, dictionary):
        super(ReportOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)


class ReportArgumentParser(resilient.ArgumentParser):
    """Helper to parse command line arguments."""

    def __init__(self, config_file=None):
        super(ReportArgumentParser, self).__init__(config_file=config_file)

        self.add_argument("--since",
                          type=valid_date,
                          help="Only report incidents created after this date (YYYY-MM-DD)")

        self.add_argument("--until",
                          type=valid_date,
                          help="Only report incidents created on or before this date (YYYY-MM-DD)")

        self.add_argument("--active",
                          action='store_true',
                          help="Only report active incidents")

        self.add_argument("--closed",
                          action='store_true',
                          help="Only report closed incidents")

        self.add_argument("--incident",
                          type=int,
                          nargs="*",
                          help="Specify one or more incident ids")

    def parse_args(self, args=None, namespace=None):
        args = super(ReportArgumentParser, self).parse_args(args, namespace)
        return ReportOpts(self.config, vars(args))


def valid_date(s):
    """Validation function for date parameters, expects YYYY-MM-DD"""
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Date must be YYYY-MM-DD: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def get_json_time(dt):
    """Epoch timestamp from datetime"""
    return timegm(dt.utctimetuple()) * 1000


def get_datetime(ts):
    """datetime from epoch timestamp"""
    if ts:
        return datetime.fromtimestamp(int(int(ts)/1000))


def all_incidents(resilient_client, opts):
    """Yield all the incidents"""
    created_since_date = opts.get("since")
    created_until_date = opts.get("until")
    currently_active = opts.get("active")
    currently_closed = opts.get("closed")
    specific_ids = opts.get("incident")
    # Query is more efficient than just reading the full description of every incident.
    # But caution: it only returns the partial incident DTO.
    conditions = [{"field_name": "inc_training", "method": "equals", "value": False}]
    if created_since_date:
        conditions.append({"field_name": "create_date", "method": "gt", "value": get_json_time(created_since_date)})
    if created_until_date:
        conditions.append({"field_name": "create_date", "method": "lte", "value": get_json_time(created_until_date)})
    if currently_active:
        conditions.append({"field_name": "plan_status", "method": "equals", "value": "A"})
    if currently_closed:
        conditions.append({"field_name": "plan_status", "method": "equals", "value": "C"})
    query = {"filters": [{"conditions": conditions}]}
    logger.debug(json.dumps(query, indent=2))
    incidents = resilient_client.post("/incidents/query?return_level=full", query)
    if specific_ids:
        incidents = [i for i in incidents if i["id"] in specific_ids]
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


def query_history(resilient_client, incident_id, query):
    """Yield history items that match a diff"""
    url = "/incidents/{}/history".format(incident_id)
    items = resilient_client.get(url)["incident_detail_history"]
    logger.debug(json.dumps(items, indent=2))
    qitems = set(query.items())
    for item in items:
        diffs = item.get("diffs", [])
        match = False
        for diff in diffs:
            try:
                if set(diff.items()) & qitems == qitems:
                    match = True
                    break
            except TypeError:
                # Can't do that set-intersection trick for list-value fields
                pass
        if match:
            yield item


def phases_report(opts, resilient_client):
    """Produce the report of time-on-phase for every incident"""
    # The list of all phases
    phase_data = resilient_client.get("/phases")
    phases = [phase["name"] for phase in phase_data["entities"]]

    with open("phases.csv", 'w') as temp:
        # Initial columns: incident id, status, timestamps
        cols = ["#", "Active?", "Date Occurred", "Date Created", "Date Confirmed"] + phases + ["Total Duration"]
        writer = csv.DictWriter(temp, fieldnames=cols, dialect='excel')
        writer.writeheader()

        for incident in all_incidents(resilient_client, opts):
            logger.info("Incident %s", incident["id"])
            start_ts = incident["create_date"]
            last_ts = incident["create_date"]
            now_ts = int(time.time() * 1000)
            end_ts = now_ts
            if incident["plan_status"] == "C":
                # incident is closed, find its end-date
                end_ts = resilient_client.get("/incidents/{}".format(incident["id"]))["end_date"]

            # Figure out time on phase from changes
            items = query_newsfeed(resilient_client, incident["id"], {"entry_type": "PHASE_CHANGE"})
            current_phase = None

            phase_duration = {"#": incident.get("id"),
                              "Active?": incident.get("plan_status"),
                              "Date Occurred": get_datetime(incident.get("inc_start")),
                              "Date Created": get_datetime(start_ts),
                              "Total Duration": float(end_ts - start_ts)/FACTOR}
            for item in sorted(items, key=lambda x: x["timestamp"]):
                timestamp = item["timestamp"]
                previous_phase = item["before"]
                current_phase = item["after"]
                duration = phase_duration.get(previous_phase, 0)
                phase_duration[previous_phase] = duration + float(timestamp - last_ts)/FACTOR
                last_ts = timestamp

            # Add the time on "current phase"
            duration = phase_duration.get(current_phase, 0)

            # Query history to find when the confirmed status changed to True
            if incident["confirmed"]:
                items = query_history(resilient_client,
                                      incident["id"],
                                      {"new_val": True, "name": "Incident Disposition"})
                try:
                    item = next(items)
                    phase_duration["Date Confirmed"] = get_datetime(item["date"])
                except StopIteration:
                    pass

            if current_phase:
                phase_duration[current_phase] = duration + float(end_ts - last_ts)/FACTOR
                writer.writerow(phase_duration)

            # print(json.dumps(phase_duration))
    print("Report written to 'phases.csv'")


def main():
    """main"""

    # Parse the commandline arguments and config file
    parser = ReportArgumentParser(config_file=APP_CONFIG_FILE)
    opts = parser.parse_args()

    # Create SimpleClient for a REST connection to the Resilient services
    resilient_client = resilient.get_client(opts)

    # Do the reports
    phases_report(opts, resilient_client)


if __name__ == "__main__":
    main()
