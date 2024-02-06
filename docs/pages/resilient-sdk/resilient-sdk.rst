.. _resilient-sdk:

=============
resilient-sdk
=============

|sdk_desc|

------------
Installation
------------

To install the IBM SOAR SDK, execute the following command:

.. code-block::

    $ pip install resilient-sdk

.. _Configuration:

+++++++++++++
Configuration
+++++++++++++

Similar to our ``resilient-circuits`` library, the SDK requires an ``app.config``
created in the default location: ``~/.resilient`` with the following minimum configurations:

.. code-block::

    [resilient]
    host=my_soar_instance.ibm.com
    org=Test Organization
    api_key_id=<id>
    api_key_secret=<secret>
    cafile=false


.. note::
    Commands that interact with the SOAR platform support the ``--config|-c`` argument, which precedes the default location. For example:

    .. code-block::

        $ resilient-sdk clone -r "Display name of Rule" "Cloned Rule display name" -c path/to/my/custom_file.config

-------------
Using the SDK
-------------

|sdk_parser_desc|

.. parsed-literal::

    usage:
    |sdk_parser_usage|

    options:
    |sdk_options|

.. _codegen:

+++++++
codegen
+++++++

|cmd_codegen_desc|

.. parsed-literal::

    usage:
    |cmd_codegen_usage|

    options:
    |cmd_codegen_options|

^^^^^^^^^^^
Basic Usage
^^^^^^^^^^^

The ``codegen`` command is your entry point with ``resilient-sdk`` to creating apps.
Once one or more functions and an associated message destination are created in the SOAR UI, running
``resilient-sdk codegen`` will generate templated python code for your app development.

The following assumes a function ``fn_my_function`` on destination ``fn_my_app`` exists in your
SOAR system. It also assumes that you've already completed the :ref:`Configuration`
section above and have a fresh Python environment to work in.

To generate an app to implement ``fn_my_function`` in a new app called ``fn_my_app``, run the following command:

.. code-block:: bash

    resilient-sdk codegen -p fn_my_app -f fn_my_function -m fn_my_app

.. note::

    Notice the ``-p`` or ``--package`` argument in the command above. This argument specifies the path
    to the package and is used throughout the ``resilient-sdk`` suite of commands. When used here to
    generate a new app, it will create a new directory in your working directory and will generate the
    contents of the app within that newly created directory.

Navigate to the newly created ``fn_my_app`` directory and have a look around. Notice that some files
at the root level pertain to app details. In particular, the ``setup.py`` file should get strong
attention. The ``setup.py`` file is where the app's details are defined and govern much of what will
appear when the app is installed in SOAR.

In the subdirectory ``fn_my_app`` you'll find the python files which make up the app. The ``components``
directory holds the function code. It is currently templated as an outline and will require that you fill it in
to fully take advantage of the function. The ``util`` directory holds the configuration information for
the app. Fill in the appropriate data in ``config.py`` to determine how the configuration section of
your app will be rendered and the ``selftest.py`` file should implement a basic connectivity check
to the endpoint, verifying proper configuration.
This document omits the details of implementing your code and testing it.
For more information on that, please seek learning resources through IBM support.

During the process, you may decide that certain elements in the UI need to be updated and pulled
into the app's package. You can achieve this with the ``--reload`` flag which automatically refreshes
any components from SOAR that have already been included in your app. You can also pull in new
components by referencing them in the command. Example:

.. code-block:: bash

    resilient-sdk codegen -p fn_my_app -pb pb_to_add_to_package --reload

After you feel comfortable with the contents of your app, you can do a validation
to make sure you're not missing anything. Run :ref:`validate` on your app:

.. code-block:: bash

    resilient-sdk validate -p fn_my_app --validate

Once you've completed the implementation of the app, run :ref:`docgen` to generate the README:

.. code-block:: bash

    resilient-sdk docgen -p fn_my_app

Then run :ref:`package` to zip the app up so that you can then publish for use:

.. code-block:: bash

    resilient-sdk package -p fn_my_app

^^^^^^^^^^^^^^
Advanced Usage
^^^^^^^^^^^^^^

Certain apps may wish to take advantage of the ability to "poll" on an endpoint. This
is useful in creating apps that bidirectionally sync between SOAR and a third party
system. Adding a poller to an app is achieved by adding the ``--poller`` flag to the
``codegen`` command when creating a new app.
This flag will generate new files in the ``/lib`` and ``/poller``
directories of the package which are intended to help you start on your way to building
a poller. In particular, find and modify the ``/poller/poller.py`` file and its associated
template files in the ``/poller/data`` subdirectory. The ``/lib/app_common.py`` file is
where common code between the poller and function files can be shared for accessing the
endpoints of the third party solution.

See :ref:`Common Poller Methods` for a guide on how to implement a poller app and
see examples of poller apps in our public
`GitHub repository <https://github.com/ibmresilient/resilient-community-apps>`_.


.. _docgen:

++++++
docgen
++++++

|cmd_docgen_desc|

.. parsed-literal::

    usage:
    |cmd_docgen_usage|

    options:
    |cmd_docgen_options|

.. _package:

+++++++
package
+++++++

|cmd_package_desc|

.. parsed-literal::

    usage:
    |cmd_package_usage|

    options:
    |cmd_package_options|

.. _validate:

++++++++
validate
++++++++

|cmd_validate_desc|

.. parsed-literal::

    usage:
    |cmd_validate_usage|

    options:
    |cmd_validate_options|

^^^^^
Usage
^^^^^

Run ``validate`` without any options to:

#. Verify that App files conform to our latest standard
#. Test that ``resilient-circuits`` starts and that the App's ``selftest`` passes
#. Run any unit tests found with ``tox`` (if installed)
#. Run a ``pylint`` scan (if installed) using our defined ``pylint`` config file
#. Run a ``bandit`` scan (if installed)  to identify any common security issues

* To ensure that all files in your App conform to our latest standard, run:

.. code-block::

    $ resilient-sdk validate -p <path_to_package> --validate

* To perform basic testing of the App, run:

.. code-block::

    $ resilient-sdk validate -p <path_to_package> --selftest

* ``validate`` also has the ability to accept an ``app.config`` file in any location. For example:

.. code-block::

    $ resilient-sdk validate -p <path_to_package> --selftest -c '/usr/custom_app.config'

* Once completed, a Markdown summary file is added to the ``dist`` directory and included in the ``.zip`` file when packaged

.. note::

    You can run each validation individually by specifying its related option.

.. _clone:

+++++
clone
+++++

|cmd_clone_desc|

.. parsed-literal::

    usage:
    |cmd_clone_usage|

    options:
    |cmd_clone_options|

.. _extract:

+++++++
extract
+++++++

|cmd_extract_desc|

.. parsed-literal::

    usage:
    |cmd_extract_usage|

    options:
    |cmd_extract_options|

.. list:

+++++++
list
+++++++

|cmd_list_desc|

.. parsed-literal::

    usage:
    |cmd_list_usage|

    options:
    |cmd_list_options|

.. _init:

++++++++
init
++++++++

|cmd_init_desc|

.. parsed-literal::

    usage:
    |cmd_init_usage|

    options:
    |cmd_init_options|

.. _SDK Changes:

----------
Change Log
----------

.. include:: ../../../resilient-sdk/CHANGES