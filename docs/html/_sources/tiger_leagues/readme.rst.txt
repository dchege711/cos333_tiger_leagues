.. _tiger_leagues_controllers:

***********
Controllers
***********

As described on `Wikipedia 
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller#Components>`_, 
the contoller receives the input, optionally validates it and then passes 
the input to the model.

Unlike the typical MVC model, we validated our most of our input in the models. 
We did this because our test suite focused on the models.

Here is a quick breakdown of the input handled by the controllers:

+---------------------------------------------+--------------------------------------------------+
| Controller                                  | Input to Relay to the Model                      |
+=============================================+==================================================+
| :py:mod:`tiger_leagues.auth`                | - Results of CAS authentication for login        |
|                                             | - Request to log out the user                    |
| (This controller uses                       |                                                  |
| :py:mod:`tiger_leagues.cas_client` to       |                                                  |
| complete its tasks)                         |                                                  |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.league`              | - Creating a new league                          |
|                                             | - Recording requests to join a league            |
|                                             | - Updating league standings                      |
|                                             | - Fetching league standings                      |
|                                             | - Fetching league matches                        |
|                                             | - Fetching player stats                          |
|                                             | - Processing score reports submitted by players  |
|                                             | - Processing player requests to leave a league   |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.admin`               | - Adding/removing players from a league          |
|                                             | - Allocating league divisions                    |
| (This controller also checks that the       | - Processing score reports submitted by admins   |
| logged in user has admin privileges)        | - Deleting a league                              |
|                                             |                                                  |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.user`                | - Fetch existing user profile                    |
|                                             | - Update a user's profile                        |
|                                             | - Post notifications to a user                   |
|                                             | - Read user's notifications                      |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.decorators`          | Used as middleware                               |
|                                             |                                                  |
|                                             | - Confirm that user is logged in                 |
|                                             | - Refresh a user's notifications                 |
+---------------------------------------------+--------------------------------------------------+

.. _controllers_design_decisions:

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
