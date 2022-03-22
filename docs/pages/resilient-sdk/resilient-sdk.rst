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

+++++++++++++
Configuration
+++++++++++++

Similar to our ``resilient-circuits`` library, the SDK it requires an ``app.config``
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


+++++++
codegen
+++++++

|cmd_codegen_desc|

.. parsed-literal::

    usage:
    |cmd_codegen_usage|

    options:
    |cmd_codegen_options|

++++++
docgen
++++++

|cmd_docgen_desc|

.. parsed-literal::

    usage:
    |cmd_docgen_usage|

    options:
    |cmd_docgen_options|

+++++++
package
+++++++

|cmd_package_desc|

.. parsed-literal::

    usage:
    |cmd_package_usage|

    options:
    |cmd_package_options|

+++++
clone
+++++

|cmd_clone_desc|

.. parsed-literal::

    usage:
    |cmd_clone_usage|

    options:
    |cmd_clone_options|

+++++++
extract
+++++++

|cmd_extract_desc|

.. parsed-literal::

    usage:
    |cmd_extract_usage|

    options:
    |cmd_extract_options|

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

----------
Change Log
----------

.. include:: ../../../resilient-sdk/CHANGES