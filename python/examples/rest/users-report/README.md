# Users and Groups Report

This sample produces a report of all users and groups in the organization.

The result is a spreadsheet (XLSX format) with two sheets:
* Users: listing all users, alphabetically, with their attributes;
* Groups, listing all groups, with their members.

Usage:

    python users_groups.py

Connection parameters are specified in `report.config` and can be
overridden with command-line options if necessary.
