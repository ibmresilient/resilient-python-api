# Introduction

This project contains utilities and sample code for the Resilient APIs
(both the Action Module and REST APIs).
The following is the top level directory structure:

 Directory  | Description
 ---------- | -----------
 docs       | Documentation and developer guides
 dotnet     | Microsoft .NET REST API examples
 java       | Java REST API and Action Module examples
 python     | Python REST API and Action Module examples
 weburl     | Web URL examples


# Example FAQ/Index

You may be here because you are looking for a specific example of accomplishing
a task or have a specific question.  This section will attempt to get you
pointed in the right direction.


## General ##

***What is the difference between the Resilient REST API and the Resilient
Action Module?***

The Resilient REST API is allows programs to get and modify data within the
Resilient system.  Using this API you can create, modify, query and delete
incident-oriented information.  The Resilient Web UI uses the REST API to do
everything.  You can write clients that use the REST API in the same ways.

The Resilient Action Module allows you to respond to "actions" (either manual
or automatic) that the server generates.  The Action Module Programmer's Guide
contains much more information about this framework.

***I need an example that I cannot find here.  Can you help?***

We love to help customers be successful! Please contact us at
[success@resilientsystems.com](mailto:success@resilientsystems.com).


## Python ##

***Where are the Python examples?***

The Python examples are located in the `python/examples` directory.
The following subdirectories exist within that directory:

* `co3` - This directory contains a Python module that is used by all of the
  Python examples.  You'll want to install this module before continuing with
  the Python examples.
* `examples/rest` - Examples showing how you can use the Resilient REST API
  with Python.
* `examples/actions` - Examples showing how to use the Resilient Action Module
  with Python.
* `examples/actions-circuits` - Examples showing how to use the Resilient Action
  Module with Python, leveraging the `resilient_circuits` application framework
  to make development simpler and more robust.
* `examples/custom-threat-service` - Examples showing how to implement a
  Custom Threat Service with Python, using the Django web framework.

See the [Python README](python/README.md) for details.

***Which version of Python do the examples use?***

They work fine with the latest release of Python 2.7 or later, or 3.4 or later.
At least Python 2.7.9 is preferred, since it has better TLS certificate handling.

***How do I run the Python examples?***

Your first step should be to install the "co3" Python module.

All of the Python examples show a command line usage if you run them with the
`--help` argument.  One key point worth calling out here is that you have to
somehow tell the example programs how to determine if the server certificate
is trusted.  You do this with the `--cafile` argument.

See the [Python README](python/README.md) for further details.


***Where can I find a Python example that just uses the REST API?***

There is such an example in `python/examples/rest/gadget/gadget.py`.
This tool is useful for exploring the REST API because it allows you to
generally GET/PUT/POST/DELETE to the Resilient server.

***Where can I find a very basic Python Action Module example?***

There is a basic example in `python/examples/actions/simple/basic.py`.
This example implements a command line interface that allows you to watch a
queue/topic.  It simply prints to the console when a message is received.
It also replies to the server with a "Processing complete" completion message.

***Where can I find a Python Action Module example that connects back to the
Resilient server using the REST API?***

There is such an example in `python/examples/actions/simple/advanced.py`.
This example builds on basic.py (mentioned above).  It connects back to the
Resilient server to append to the incident's description.

***What is Circuits?***

The [Circuits framework](http://circuitsframework.com/) is a lightweight,
event-driven, asynchronous framework for Python applications.

Resilient provides a Circuits-based application structure, `resilient_circuits`,
for developing Action Module integrations in Python.  This framework can easily
load and run multiple "components" at once, to support your integration and
automation tasks.  It can be a very convenient and productive way to develop
applications that use Resilient REST API and Resilient Action Module.

See the [resilient-circuits README](python/resilient-circuits/README) and the
[extensive examples](python/examples/actions-circuits/) for further details.



## Java ##

***Where are the Java examples?***

The Java examples are in the `java/examples` directory.
The following subdirectories exist within that directory:

* `examples/caf/general` - Groovy examples that read Action Module actions from
  a destination and invoke Resilient REST API commands.
* `examples/caf/camel` - Apache Camel example that reads Action Module actions
  from a destination and adjusts the incident severity based on the incident
  type.
* `examples/caf/mulesoft` - Mulesoft Anypoint Studio example that illustrates
  how to read from a message destination and post to HipChat.  Note that you
  will need to install Mulesoft Anypoint Studio to use this example.
* `examples/rest` - A collection of examples that illustrate various ways to use
  the Resilient REST API.
* `jms-util` - A library that allows for secure connections to Apache ActiveMQ
  servers.  All of the Action Module examples use this library because the
  default Active MQ client library does not check for certificate common name
  mismatch errors.

See the [Java README](java/README.md) for more information.

***What Java version do the examples use?***

The examples were written using Java 7, although you should be able to run them
with Java 6 - 8.

Some of the examples are written in Groovy v2.3.6.

***How do you build the examples?***

We use Gradle to build the examples.
See the [Java Examples README](java/examples/README.md) for more information.

***What's the best way to explore the Java examples?***

We highly recommend that you use Eclipse or IntelliJ for this.  You will need
to have the Gradle Eclipse add-in installed.  Once you have done that, you can
import the Gradle project in the "java" directory.

***What is Mulesoft?***

[Mulesoft](https://www.mulesoft.org) is an Enterprise Service Bus (ESB) that
allows you to run multiple integrations (Resilient-related or not) within a
single environment.  An ESB can be helpful if you have many different systems
that need to interact with one anohter.  If you already have an ESB, you may
want to consider having your Resilient integrations run within it.

The Mulesoft ESB also has a number of pre-built connectors that might simplify
integrations with Resilient.

See the [Mulesoft HipChat Example](java/examples/caf/mulesoft/) for an example
of how you can use Mulesoft to integrate Resilient with a chat client (HipChat
in our example).

If you do not need to full power of an ESB such as Mulesoft, you may wish to
consider a lighter-weight alternative such as Apache Camel (see below).

***What is Apache Camel?***

Camel allows you to create "routes" that describe how messages (such as Action
Module messages) get processed.  Apache Camel is an open source tool with
built-in connectors that may help simplify integrations with Resilient.

See the [Apache Camel Example](java/examples/caf/camel) section for an example
of how you can use Camel to integrate with Resilient.
