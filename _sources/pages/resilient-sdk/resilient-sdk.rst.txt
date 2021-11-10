=============
resilient-sdk
=============

Python SDK for developing Apps for the IBM SOAR (Resilient) Platform

------------
Installation
------------

To install the IBM SOAR (Resilient) SDK, simply execute the following command:

.. code-block::

    $ pip install resilient-sdk

+++++++++++++
Configuration
+++++++++++++

Similar to our ``resilient-circuits`` library, to configure the SDK it requires an ``app.config``
created in the default location: ``~/.resilient`` with the following minimum configurations:

.. code-block::

    [resilient]
    host=my_soar_instance.ibm.com
    org=Test Organization
    api_key_id=<id>
    api_key_secret=<secret>
    cafile=false


.. note::
    Any of our commands that interact with the Platform support a ``--config|-c`` argument that precedes the default location, for example:

    .. code-block:: 

        $ resilient-sdk clone -r "Display name of Rule" "Cloned Rule display name" -c path/to/my/custom_file.config

-------------
Using the SDK
-------------

|sdk_desc|

.. parsed-literal::

    usage:
    |sdk_usage|

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

----------
Change Log
----------

.. include:: ../../../resilient-sdk/CHANGES