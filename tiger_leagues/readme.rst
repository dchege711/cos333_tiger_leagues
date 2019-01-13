.. _tiger_leagues_controllers:

***********
Controllers
***********

As described on `Wikipedia 
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller#Components>`_, 
the contoller receives the input, optionally validates it and then passes 
the input to the model.

.. _design_decisions:

Design Decisions
----------------

.. _use_of_decorators:

Use of Decorators
^^^^^^^^^^^^^^^^^

We extensively used decorators, as defined in 
:py:mod:`tiger_leagues.decorators`, to enforce access control, e.g. only 
logged in users can join a league, only admins can accept/reject league 
members, etc.

.. _graceful_error_handling:

Graceful Error Handling
^^^^^^^^^^^^^^^^^^^^^^^

Since we defined a custom exception class, 
:py:mod:`tiger_leagues.models.exception`, we were able to set an error handler 
for any such exception. This allows us to gracefully show helpful error pages/
responses instead of the default ones.

.. _controllers_documentation:

Controllers Documentation
-------------------------

tiger_leagues.auth
^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.auth
   :members:

tiger_leagues.cas_client
^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.cas_client
   :members:

tiger_leagues.admin
^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.admin
   :members:

tiger_leagues.league
^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.league
   :members:

tiger_leagues.user
^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.user
   :members:

tiger_leagues.decorators
^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.decorators
   :members:

tiger_leagues.wsgi
^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.wsgi
   :members:
