# Circuits Framework

This example uses the [Circuits framework](http://circuitsframework.com/) to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

This provides a simple, extensible structure to support a single long-running
application that handles a variety of manual and automatic actions.

The main application, [app.py](app.py), creates a single Circuits [component](http://circuits.readthedocs.org/en/latest/man/index.html)
for the application, then creates various other components to handle
Actions Module events, and registers them with the application so that they
are called asynchronously when events occur.

The [sample_components.py](sample_components.py) shows several different
components that handle Actions Module events and also that use the Resilient
REST API.

Each component has a *channel*, which is the name of the
Message Destination that the component should listen on.  The framework
automatically subscribes to these message queues and listens for messages.

Each component then implements *message handler* methods, which are called
when an Actions Module message arrives.  In this framework, the name of the
message handler method is simply the name of the Custom Action (lowercase,
with underscores replacing spaces).  So if you define a manual action called
"Investigate Logs", the framework will run the function `investigate_logs()`
on your component when the user initiates this action.


## Setup

The script expects the following sample actions, which can be either manual
or automatic:

* An artifact action named "Artifact Sample", with message destination `sample`.
  When run, this sets the incident's description to the artifact's value.

* A task action named "Task Sample", with message destination `sample`.
  When run, this demonstrates exception handling: it produces an error message
  that can be seen in the Resilient application by opening the "Action Status"
  dialog.

* Any action(s) with message destination `sample2`.  A sample component
  registers for all actions on this queue or topic, logs a message when they
  are fired, and returns the name of the action for the "Action Status" dialog.

* An action named "sample_action", with message destination `queue3`.  The
  sample code demonstrates how to register a component whose message destination
  is set dynamically.  When triggered, this action returns "ok", and the console
  logs an informational message.


### Running the example

Edit the `app.config` file with parameters appropriate to your environment.

Then run the action script:

    python app.py

To trigger actions:  open an incident, then pen the custom actions menu for this
incident or its tasks or artifacts, then select the actions defined above.
The action script log will print a message for each action that is processed.
