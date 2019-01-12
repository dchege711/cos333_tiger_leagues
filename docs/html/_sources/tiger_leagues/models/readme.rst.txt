.. _tiger_leagues_models:

******
Models
******

As described on `Wikipedia 
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller#Components>`_, 
the model is the application's dynamic data structure, independent of the user 
interface. It directly manages the data, logic and rules of the application.

.. _notes:

Notes
-----

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



tiger_leagues.models.db_model
-----------------------------
.. automodule:: tiger_leagues.models.db_model
   :members:

tiger_leagues.models.config
---------------------------
.. automodule:: tiger_leagues.models.config
   :members:

tiger_leagues.models.league_model
---------------------------------
.. automodule:: tiger_leagues.models.league_model
   :members:

tiger_leagues.models.admin_model
--------------------------------
.. automodule:: tiger_leagues.models.admin_model
   :members:

tiger_leagues.models.user_model
-------------------------------
.. automodule:: tiger_leagues.models.user_model
   :members:

tiger_leagues.models.exception
------------------------------
.. automodule:: tiger_leagues.models.exception
   :members:
