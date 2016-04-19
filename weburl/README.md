# Web URL

The Resilient Incident Response Platform supports a rich variety of programmable
interfaces that can be used for integration with other systems.

The simplest of these interfaces is the Web URL.

By directing a user’s browser to specially-constructed Web URLs, the user can be
guided through automatic creation of an incident, and other functions.
A typical use case for this integration is in manually creating Resilient
incidents from within another system, such as a SIEM. This streamlines the
process of escalation to the incident response team.

See the [Web URL Integration Guide](../docs/Web URL Integration Guide.pdf) for
further details.

# URL Construction Examples

The [examples](examples) folder contains two HTML files that you can use to
interactively build Web URLs: [new_by_url](examples/new_by_url.html) to create
a URL for a new incident based on values you supply, and
[add_artifacts_by_url](examples/add_artifacts_by_url.html) to create a URL for
adding one or more artifacts to an existing incident.

Open these in a Web browser to interactively explore Web URL construction.

Use the source code (HTML and JavaScript) to understand how the URL parameters
are constructed.
