=============
resilient-lib
=============

|lib_desc|

-----
Usage
-----

``resilient-lib`` is now a direct dependency of ``resilient-circuits`` as of **v40.0** to help make development more streamlined

It can also be installed directly with:

.. code-block::

   $ pip install resilient-lib

To use it within your App development, **import** it like any other Python Package:

.. code-block:: python

   from resilient_lib import readable_datetime

   created_date = readable_datetime(fn_inputs.inc_create_date, rtn_format="%m-%d-%Y %H:%M:%S")

-------
Proxies
-------

``resilient-lib`` supports an ``[integrations]`` section in your app.config file.
Add this section to define proxy settings to be used for all integrations that use this library.

.. code-block::

   [integrations]
   # These proxy settings will be used by all integrations. 
   # To override, add any parameter to your specific integration section
   http_proxy=
   https_proxy=
   timeout=30


.. note::
   If your app is running on App Host 1.6 or greater, you can take advantage of
   the global proxy functionality. There is no need to add an ``[integrations]``
   section like above. Run the following on your App Host for more information:

   .. code-block::

      $ manageAppHost proxy -h

   *The hierarchy of proxies is as follows:*

   #. **RequestsCommon.execute() Function:** the ``proxies`` parameter.
   #. **Environmental Variables:** ``HTTPS_PROXY``, ``HTTP_PROXY`` and ``NO_PROXY`` set
      using the ``manageAppHost proxy`` command on the App Host.
   #. **Function Options:** ``http_proxy`` or ``https_proxy`` configs set in the
      **Function Section** (``[my_function]``) of your app.config file.
   #. **Integrations Options:** ``http_proxy`` or ``https_proxy`` configs set in the
      **Integrations Section** (``[integrations]``) of your app.config file.

---------------------
Common Helper Methods
---------------------

.. automodule:: resilient_lib.components.resilient_common
   :members:

.. autoclass:: resilient_lib.components.html2markdown::MarkdownParser
.. autofunction:: resilient_lib.components.html2markdown::MarkdownParser.convert

.. automodule:: resilient_lib.components.oauth2_client_credentials_session
   :members:

----------------------
Common Request Methods
----------------------

.. autoclass:: resilient_lib.components.requests_common::RequestsCommon
.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.execute
.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.get_proxies


--------------------
Common Jinja Methods
--------------------

.. automodule:: resilient_lib.components.templates_common
   :members:
   :exclude-members: environment

----------
Exceptions
----------

.. autoexception:: resilient_lib.components.integration_errors::IntegrationError

----------
Change Log
----------

.. include:: ../../../resilient-lib/CHANGES

