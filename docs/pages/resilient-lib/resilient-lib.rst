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

You can now take advantage of the global proxy functionality.
There is no need to add an ``[integrations]`` section like below.
Run the following on your App Host for more information:

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


If using a version of App Host earlier than 1.6, ``resilient-lib`` supports an ``[integrations]`` section in your app.config file.
Add this section to define proxy settings to be used for all integrations that use this library.

.. code-block::

   [integrations]
   verify=True
   # These proxy settings will be used by all integrations. 
   # To override, add any parameter to your specific integration section
   http_proxy=
   https_proxy=
   timeout=30

------------------------
Certificate Verification
------------------------

You can now take advantage of the global verify functionality.
Valid options for ``verify`` are True, False, or a path to a
valid certificate chain file. The default (and suggested value)
is ``True`` which will use the default Python CA bundle found at
``REQUESTS_CA_BUNDLE``.

*The hierarchy of proxies is as follows:*

#. **RequestsCommon.execute() Function:** the ``verify`` parameter.
#. **Function Options:** ``verify`` config set in the
   **Function Section** (``[my_function]``) of your app.config file.
#. **Integrations Options:** ``verify`` config set in the
   **Integrations Section** (``[integrations]``) of your app.config file.

Example:

.. code-block::

   [my_function]
   verify=/var/rescircuits/cafile.pem
   http_proxy=
   https_proxy=
   timeout=30

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
.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.get_verify
.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.get_client_auth
.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.get_timeout
.. autoclass:: resilient_lib.components.requests_common::RequestsCommonWithoutSession


---------------------
Common Poller Methods
---------------------

.. autofunction:: resilient_lib.components.poller_common::poller
.. automodule:: resilient_lib.components.poller_common
   :members:
   :exclude-members: s_to_b, b_to_s, get_last_poller_date, _get_timestamp, poller, get_template_dir, update_soar_cases


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

