==================
resilient-circuits
==================

|circuits_desc|. Contains the class :class:`~resilient_circuits.app_function_component.AppFunctionComponent`
that gets generated using the ``codegen`` command in the ``resilient-sdk``

----------
Components
----------

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
