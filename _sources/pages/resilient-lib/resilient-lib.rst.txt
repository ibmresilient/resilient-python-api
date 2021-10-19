=============
resilient-lib
=============

This Python Package contains common library calls which facilitate the development of Apps for IBM SOAR

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

^^^^^^^
Proxies
^^^^^^^

``resilient-lib`` supports an ``[integrations]`` section in your app.config file. 
Add this section to define proxy settings which will be used for all integrations which use this library:

.. code-block::

   [integrations]
   # These proxy settings will be used by all integrations. 
   # To override, add any parameter to your specific integration section
   http_proxy=
   https_proxy=
   timeout=30


.. note::
   If your App is running on AppHost 1.6 or greater you can take advantage of the
   the global proxy functionality and there is no need to add an ``[integrations]``
   section like above. Run the following on your AppHost for more:

   .. code-block::

      $ manageAppHost proxy -h

---------------------
Common Helper Methods
---------------------

.. automodule:: resilient_lib.components.resilient_common
   :members:

.. .. automodule:: resilient_lib.components.html2markdown
   :members:

.. .. automodule:: resilient_lib.components.oauth2_client_credentials_session
   :members:

----------------------
Common Request Methods
----------------------

.. note::
   As of version 41.1 in the Atomic Function template ``RequestsCommon`` is available 
   in a class that inherits ``resilient_circuits.AppFunctionComponent`` as an ``rc`` attribute:

   .. code-block:: python

      response = self.rc.execute(method="get", url=ibm.com)

.. .. autofunction:: resilient_lib.components.requests_common::RequestsCommon.execute

----------
Change Log
----------

.. include:: ../../../resilient-lib/CHANGES

