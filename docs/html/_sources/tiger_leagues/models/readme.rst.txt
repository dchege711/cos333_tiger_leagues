.. _tiger_leagues_models:

******
Models
******

As described on `Wikipedia 
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller#Components>`_, 
the model is the application's dynamic data structure, independent of the user 
interface. It directly manages the data, logic and rules of the application. 
We deviated a bit from the standard MVC architecture by validating our inputs 
at this level.

Here is a quick breakdown of where the higher-level application logic is handled:

+---------------------------------------------+--------------------------------------------------+
| Model                                       | Application Logic                                |
+=============================================+==================================================+
| :py:mod:`tiger_leagues.models.league_model` | - Creating a new league                          |
|                                             | - Recording requests to join a league            |
|                                             | - Updating league standings                      |
|                                             | - Fetching league standings                      |
|                                             | - Fetching league matches                        |
|                                             | - Fetching player stats                          |
|                                             | - Processing score reports submitted by players  |
|                                             | - Processing player requests to leave a league   |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.models.admin_model`  | - Adding/removing players from a league          |
|                                             | - Allocating league divisions                    |
|                                             | - Processing score reports submitted by admins   |
|                                             | - Deleting a league                              |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.models.user_model`   | - Fetch existing user profile                    |
|                                             | - Update a user's profile                        |
|                                             | - Post notifications to a user                   |
|                                             | - Read user's notifications                      |
+---------------------------------------------+--------------------------------------------------+
| :py:mod:`tiger_leagues.models.exception`    | - Raise exceptions caused by errors encountered  |
|                                             |   when accomplishing any of the above logic      |
+---------------------------------------------+--------------------------------------------------+

.. _models_design_decisions:

Design Decisions
----------------

.. _application_context:

Application Context
^^^^^^^^^^^^^^^^^^^

Tiger Leagues can be ran in 3 different contexts. We used environment 
variables and :py:mod:`tiger_leagues.models.config` to switch between the 
different contexts:

* Development

Occurs when Tiger Leagues is being ran locally. We found it convenient to use 
a locally hosted database so that the dev can modify its content as they see 
fit.

* Travis CI

Our tests write and read data from the database. We found it convenient to 
use a PostgreSQL database that is provisioned by Travis CI. The database is 
set up by the ``.travis.yml`` file at the root of the repository.

* Heroku (Production)

If Tiger Leagues is running on Heroku, we use the database provided by Heroku.

.. _league_standings:

League Rankings
^^^^^^^^^^^^^^^

Initially, we'd compute the rankings of players from the matches table. This 
was motivated by reducing redundancy in the database. However, we hypothesized 
that users will view the rankings way more frequently than update scores.

We therefore decided to add another table, ``league_standings`` that contains 
the most recent rankings that incorporate all the approved score reports. 
Although this creates some redundancy (we could determine the rankings from 
the score reports), it allows us to reduce repeated computation.

.. _keeping_the_user_updated:

Keeping the User Updated
^^^^^^^^^^^^^^^^^^^^^^^^

Since the users are not isolated, it's important to keep a user updated of any 
developments that involve them. For instance, a user might get their join 
request approved/denied by an admin. Or the score for a given match might have 
been reported by the other player and the admin approved of it.

We therefore developed a rudimentary notification system in which we post 
relevant updates to a user's mailbox. The system does not allow for responses. 
We leave that for future implementations of Tiger Leagues.

.. _models_documentation:

Models Documentation
--------------------

tiger_leagues.models.db_model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.db_model
   :members:

tiger_leagues.models.config
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.config
   :members:

tiger_leagues.models.league_model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.league_model
   :members:

tiger_leagues.models.admin_model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.admin_model
   :members:

tiger_leagues.models.user_model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.user_model
   :members:

tiger_leagues.models.exception
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: tiger_leagues.models.exception
   :members:
