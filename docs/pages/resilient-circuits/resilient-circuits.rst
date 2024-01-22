==================
resilient-circuits
==================

|circuits_desc|. 

----------
Commands
----------

``resilient-circuits`` exposes the following commands:

***
run
***

Start up resilient-circuits in a local integration server environment.

Run resilient-circuits:

.. code-block:: bash

    $ resilient-circuits run

Run resilient-circuits in DEBUG mode:

.. code-block:: bash

    $ resilient-circuits run --loglevel=DEBUG

******
config
******

Manage configuration file app.config (integration server only). Default location is ``~/.resilient/app.config``

Create the app.config file in the default location:

.. code-block:: bash

    $ resilient-circuits config -c

Update the app.config file with newly installed apps:

.. code-block:: bash

    $ resilient-circuits config -u


Contains the class :class:`~resilient_circuits.app_function_component.AppFunctionComponent`
that gets generated using the :ref:`codegen` command in the :ref:`resilient-sdk`

----------
Components
----------

``resilient-circuits`` also provides the high level Python API which each app function is built off of.

.. autoclass:: resilient_circuits.app_function_component::AppFunctionComponent
   :members: __init__, get_fn_msg, status_message

.. autofunction:: resilient_circuits.actions_component::ResilientComponent.rest_client

----------
Decorators
----------

.. autodecorator:: resilient_circuits.decorators::app_function


----------
Helpers
----------

.. autofunction:: resilient_circuits.helpers::is_this_a_selftest

----------
Change Log
----------

.. include:: ../../../resilient-circuits/CHANGES
