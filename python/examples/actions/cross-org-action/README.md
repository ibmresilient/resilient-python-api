# Cross-Organization Escalation

This example demonstrates escalation of an incident from one organization
to another, using the Action Module.

Where the original incident has an artifact that should be
investigated by a specialist team that uses a separate Resilient Organization
(or a completely separate Resilient application instance), a custom action
can take the artifact, and information from the original incident, and
create a new incident in the destination organization.

When the action is run, it creates a Milestone in the original incident's
timeline, indicating that a significant event occurred.  It also creates a
Milestone in the new incident created in the destination organization.

The code also demonstrates how to copy attachments and notes (including the
parent-child hierarchy in notes) from one incident to another.

## Setup

You need two organizations, or two Resilient appliances.

In the default configuration (see `crossorg.config`), the originating org
is *Culture* and the destination org is *Special Circumstances*.

In the *Culture* org, you must set up the custom action:

* Open the Customization Settings page, then select the Message Destinations tab
* Add a message destination, type Queue, with programmatic name `crossorg`,
  and add the API user to the queue's user list.
      ![Destination](documentation/messagedestination.png)
  
* Create the following Action Fields:

    * "New Incident Description", with API Access Name `new_incident_description`,
      type Text Area.  The value that users enter in this field will become
      the description of the new incident in the destination org.

      ![Action field](documentation/new_incident_description.png)

    * "New Incident Type", with API access name `new_incident_type`,
      type Select, with values: "Malware", "Phishing", and any other values
      appropriate for escalation.  These values must correspond to incident
      types that are defined in the destination organization.

      ![Action field](documentation/new_incident_type.png)

    * Optionally: a boolean field `copy_attachments`.  This will allow users to
      choose whether attachments are copied onto the new incident.
    * Optionally: a boolean field `copy_notes`.  This will allow users to
      choose whether notes are copied onto the new incident.


* Create a Menu Item Rule, "Escalate to Special Circumstances" (or whatever name
  you choose).  Set the object type to Artifact.  Add the queue `crossorg` to the
   destinations.  Create "New Incident Type" and "New Incident Destination"
  action fields (and optionally the "copy_attachments" and "copy_notes" fields) to the layout.

  ![Custom manual action](documentation/manual_action.png)



### Running the example

Edit the `crossorg.config` file with parameters appropriate to your environment:

* The credentials for connecting to your originating organization
* The name of your destination organization
* The credentials for connecting to your destination organization
  (if different)

Then run the action script:

    python crossorg.py

To trigger the action:  open an incident in the *Culture* org, and
add an artifact.  Open the custom actions menu for this artifact,
and select "Escalate to Special Circusmtances".

The action script log will show information such as:

    2015-07-30 10:29:34,589 Received action 19 for incident 2238: type=Artifact; name=Incident ABCD
    2015-07-30 10:29:34,589 new_incident_from_artifact: Description, type 1350
    2015-07-30 10:29:36,478 Created new incident: 2258
    2015-07-30 10:29:36,777 Created new artifact: [] on incident: 2258
    2015-07-30 10:29:37,228 Created new milestone: 11 on incident: 2238
    2015-07-30 10:29:37,458 Created new milestone: 12 on incident: 2258
    2015-07-30 10:29:38,180 note: {'text': u'<div>note</div>'}
    2015-07-30 10:29:38,411 note: {'text': u'<div>reply</div>', 'parent_id': 150}
    2015-07-30 10:29:38,661 Sending frame cmd='SEND' headers={'destination': '/queue/acks.201.crossorg', 'correlation-id': 'invid\\c152'}
    2015-07-30 10:29:38,662 Received frame: 'MESSAGE', headers={'reply-to': '/queue/acks.201.crossorg', 'expires': '0', 'timestamp': '1438200819047', 'destination': '/queue/actions.201.crossorg', 'correlation-id': 'invid:152', 'persistent': 'true', 'priority': '4', 'Co3MessagePayload': 'ActionDataDTO', 'Co3ContentType': 'application/json', 'message-id': 'ID:resilient-49759-1438192165135-3:2:11:1:1', 'Co3ContextToken': 'eyJhbGciOiJIUzI1NiJ9.eyJhY3Rpb25zIjpbMTldLCJleHBpcmF0aW9uRGF0ZSI6MTQzODI4NzIxODUxNn0.VLWJws4LTdPoR17O5gaNwKSK224peGnnTXMyU123Hsw', 'subscription': 'stomp_listener'}, len(body)=6153

The original incident will show a new milestone,

![Milestone](documentation/milestone.png)

Then switch to the *Special Circumstances* organization, and you will see the new incident.
