"""
wsgi.py

Expose Flask application object as the WSGI application. The WSGI app will then
be ran by a WSGI server. Flask's built-in server is not suitable for production.

In our case, in ``../Procfile``, we ask ``gunicorn`` to use the ``app`` object 
that is exposed in the ``tiger_leagues`` module. 

http://flask.pocoo.org/docs/1.0/deploying/

"""

import tiger_leagues
app = tiger_leagues.create_app()
