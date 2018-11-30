"""
db.py

This file acts as the central access to the database.

"""

# add a helper function that catchs database errors

import sys
import atexit
from psycopg2 import connect, ProgrammingError, extras
from . import config

class Database:
    """
    Represents a connection to the Tiger Leagues database.
    """

    def __init__(self):
        """
        Initialize the database instance.

        """
        self._connection = connect(config.DATABASE_URL)
        self.launch()
        atexit.register(self.disconnect)

    def disconnect(self):
        """
        Close the connection to the database. Should be called before exiting 
        the script.
        """
        self._connection.close()
    
    def launch(self):
        """
        Initialize the tables if they do not exist yet.
        """
        self.execute((
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id SERIAL PRIMARY KEY, name VARCHAR(255), net_id VARCHAR(255), "
            "email VARCHAR(255), phone_num VARCHAR(255), room VARCHAR(255), "
            "league_ids TEXT);"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS match_info ("
            "match_id SERIAL PRIMARY KEY, user_id_1 INT, user_id_2 INT, league_id INT, "
            "score_user_1 INT, score_user_2 INT, deadline DATE);"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS league_info ("
            "league_id SERIAL PRIMARY KEY, league_name VARCHAR(255), "
            "description TEXT, points_per_win INT, points_per_draw INT, "
            "points_per_loss INT, registration_deadline DATE, "
            "additional_questions TEXT);"
        ))

    def execute(self, stmtstr, values=None, cursor_factory=extras.DictCursor):
        """
        @returns `Cursor` after executing the SQL statement in `stmtstr` with 
        placeholders substituted by the `values` tuple. 
        
        @returns `None` if the SQL transaction fails. The error is reported to 
        stderr and the transaction is rolled back.
        """
        cursor = self._connection.cursor(cursor_factory=cursor_factory)
        try:
            if values is not None: cursor.execute(stmtstr, values)
            else: cursor.execute(stmtstr)
            self._connection.commit()
            return cursor
        except ProgrammingError as error:
            print(error, file=sys.stderr)
            self._connection.rollback()
            return None
            
    def iterator(self, cursor):
        """
        @description Alternative to having the `x = cursor.fetchone()` ... 
        `while x is not None` every time that we're iterating through DB results

        @yields a row fetched from the cursor.
        """
        row = cursor.fetchone()
        while row is not None:
            yield row
            row = cursor.fetchone()
