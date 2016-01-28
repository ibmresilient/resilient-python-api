# Actions Module Examples

This directory contains simple example Actions Module processors written in
Python.  It assumes you have installed the `co3` helper module (see
[/python/co3/README](../../co3/README) for instructions on how to install
the `co3` module).

These scripts were written to support either Python 2 or 3.
Python 3 has better TLS certificate validation built in and is recommended
for new applications.

### Configuration settings

These utilities read their settings from an optional configuration file,
`samples.config`.  The settings can be overridden by specifying them on the
command line.  If the password is not specified, you will be prompted.
Use the `--help` option to see the valid parameters.

## basic.py

The basic.py script does the following:

  * Connects to the Resilient server on port 65001 using the STOMP protocol
  * Illustrates the correct way to validate the server certificate
  * Waits for messages on the specified message destination
  * When a message is received, it displays the incident ID, name and severity text.
  * Illustrates how you can use the message's metadata to convert ID values to text.
  * Shows how to reply/acknowledge the message (so that a message appears in the
    Resilient Action Status page).

You start the processor from the command line.  To print the usage, do this:

```
  python basic.py --help
```

The following is an example usage.  In this example, we are connecting to a host
named co3.xyz.com using a user name of user@xyz.com.  The message destination's
programmatic name is "test" and the organization ID is 201.  The `cacerts.pem`
file contains the trusted CA certificates.  You will be prompted to enter your
password.

```
  $ python basic.py --cafile cacerts.pem --host co3.xyz.com --email user@xyz.com actions.201.test
```

## advanced.py

The `advanced.py` script is similar to `basic.py`, but it also shows how to
connect back to the Resilient server using the Resilient REST API.
In this example, it simply updates the incident description to include the time.

It is worth noting that when updating an incident, you must consider the
possibility that another user has updated the same incident in the meantime.
This script handles that by using the `SimpleClient.get_put` method, which
accepts a function that applies the changes to the incident.  The `get_put`
method does a `get`, calls the `apply` function, then performs the `put`.
If the `put` fails with a 409 Conflict error, then the get/apply/put is tried
again.

You start the processor from the command line.  To print the usage, do this:

```
  python advanced.py --help
```

The usage is identical to the basic.py script, except that since it connects to
the Resilient server using the REST API, you may need to specify the `--org`
option (if your user is in multiple Resilient organizations).


## Topics and Queues

Queues are referenced as `actions.<org_id>.<queue_programmatic_name>`.
For example, `actions.201.test`.

Topic message destinations are also supported, for cases where you want to
send Action Module messages to all active subscribers, and drop the messages
if no subscribers are active.  To refer to a topic, use the name:

    /topic/actions.<org_id>.<queue_programmatic_name>


## Resilient-Circuits Framework

The 'basic' and 'advanced' examples in this directory show how to interact with
Action Module message destinations directly, subscribing with the STOMP
protocol.

For production applications, we recommend using the [/python/resilient-circuits](../../resilient-circuits/)
framework.  This is a simple event-based application framework that manages
the queue and message handling functions, and just calls methods in your
Python class when an event arrives.
