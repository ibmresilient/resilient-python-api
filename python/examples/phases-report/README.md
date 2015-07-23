# History Reports

This sample produces a report by querying the history of each incident,
and counting the time between phase-change events in that history.
The result is a CSV file with one row per incident, with a column
for each phase that shows the number of hours the incident was (or is)
active in that phase.

Usage:

    python report.py [--since 2015-01-31]

Connection parameters are specified in `report.config` and can be
overridden with command-line options if necessary.
