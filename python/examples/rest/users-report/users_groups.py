#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Report users and groups into a spreadsheet"""

from __future__ import print_function
import os
import logging
from openpyxl import Workbook
from openpyxl.styles import Font
from resilient_circuits import keyring_arguments
from resilient_circuits import rest_helper


# The config file location should usually be set in the environment
APP_CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "report.config")


def report_users_and_groups(client, filename="users_groups.xlsx"):
    """Produce a spreadsheet report of the users and groups in this organization"""
    # Get the lists of users and groups
    users = client.get("/users?want_disabled=true")
    groups = client.get("/groups")

    # Make lookups for convenience
    users_lookup = {user["id"]: user["email"] for user in users}
    groups_lookup = {group["id"]: group["name"] for group in groups}

    # Sort users by last name
    users = sorted(users, key=lambda user: user["lname"] + user["fname"])
    # Sort groups by name
    groups = sorted(groups, key=lambda group: group["name"])

    # Create a spreadsheet that lists them all

    workbook = Workbook()
    ws_users = workbook.active
    ws_users.title = "Users"
    ws_groups = workbook.create_sheet(title="Groups")

    users_column_map = {
        "id": 1,
        "email": 2,
        "fname": 3,
        "lname": 4,
        "title": 5,
        "phone": 6,
        "enabled": 7,
        "status": 8,
        "group_ids": 13
    }
    users_role_column_map = {
        "administrator": 9,
        "create_incs": 10,
        "master_administrator": 11,
        "observer": 12
    }
    groups_column_map = {
        "id": 1,
        "name": 2,
        "members": 3
    }

    # Users sheet: make the header row
    row = 1
    for col in users_column_map:
        ws_users.cell(row=row, column=users_column_map[col], value=col).font = Font(bold=True)
    for col in users_role_column_map:
        ws_users.cell(row=row, column=users_role_column_map[col], value=col).font = Font(bold=True)

    # Write the user rows
    for user in users:
        row = row + 1
        for col in users_column_map:
            value = user.get(col)
            if col == "group_ids":
                # resolve names of all the groups
                user_groups = sorted([groups_lookup.get(group, "?") for group in value])
                value = ", ".join(user_groups)
            ws_users.cell(row=row, column=users_column_map[col], value=value)
        for col in users_role_column_map:
            value = user["roles"].get(col)
            value = "Y" if value else ""
            ws_users.cell(row=row, column=users_role_column_map[col], value=value)

    # Groups sheet: make the header row
    row = 1
    for col in groups_column_map:
        ws_groups.cell(row=row, column=groups_column_map[col], value=col).font = Font(bold=True)

    # Write the group rows
    for group in groups:
        row = row + 1
        for col in groups_column_map:
            value = group.get(col)
            if col == "members":
                # resolve names of all the users
                group_users = sorted([users_lookup.get(user, "?") for user in value])
                value = ", ".join(group_users)
            ws_groups.cell(row=row, column=groups_column_map[col], value=value)

    workbook.save(filename=filename)
    print("Written to {}".format(filename))


def main():
    """Main"""
    # Parse the commandline arguments and config file
    parser = keyring_arguments.ArgumentParser(config_file=APP_CONFIG_FILE)
    opts = parser.parse_args()

    # Create SimpleClient and connect
    resilient_client = rest_helper.get_resilient_client(opts)

    # Report the list of users and groups
    report_users_and_groups(resilient_client)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    main()
