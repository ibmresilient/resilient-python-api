=============
resilient-lib
=============

This Python Package contains common library calls which facilitate the development of Apps for IBM SOAR

-----
Usage
-----

``resilient-lib`` is now a direct dependency of ``resilient-circuits`` as of v40.0 to help make development more streamlined

To use it within your App development, **import** it like any other Python Package:

.. code-block:: python

   from resilient_lib import get_file_attachment, get_file_attachment_name
   TODO give examples of execute and tab imports too


---------------------
Common Helper Methods
---------------------

.. automodule:: resilient_lib.components.resilient_common
   :members:

----------------------
Common Request Methods
----------------------

.. note::
   As of version 41.1 in the Atomic Function template ``RequestsCommon`` is available 
   in a class that inherits ``resilient_circuits.AppFunctionComponent`` as an ``rc`` attribute:

   .. code-block:: python

      response = self.rc.execute(method="get", url=ibm.com)

.. autofunction:: resilient_lib.components.requests_common::RequestsCommon.execute

----------
Change Log
----------

.. include:: ../../../resilient-lib/CHANGES

