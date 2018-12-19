"""
db.py

This file acts as the central access to the database.

"""

from warnings import warn
import atexit
from psycopg2 import connect, extras, sql
from .. import config

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
            "division_id INT, score_user_1 INT, score_user_2 INT, "
            "status VARCHAR(255), deadline DATE, status VARCHAR(70));"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS league_info ("
            "league_id SERIAL PRIMARY KEY, league_name VARCHAR(255), "
            "description TEXT, points_per_win INT, points_per_draw INT, "
            "points_per_loss INT, registration_deadline DATE, max_num_players INT, "
            "creator_user_id INT NOT NULL, match_frequency_in_days NUMERIC DEFAULT 7.0, "
            "additional_questions TEXT);"
        ))

    def execute(self, statement, values=None, dynamic_table_or_column_names=None, 
        cursor_factory=extras.DictCursor):
        """
        @returns `Cursor` after executing the SQL statement in `statement` with 
        placeholders substituted by the `values` tuple. 
        
        @returns `None` if the SQL transaction fails. The error is reported to 
        stderr and the transaction is rolled back.
        """
        cursor = self._connection.cursor(cursor_factory=cursor_factory)
        try:
            if dynamic_table_or_column_names:
                cursor.execute(
                    sql.SQL(statement).format(*[
                        sql.Identifier(s) for s in dynamic_table_or_column_names
                    ]),
                    values
                )
            else: 
                cursor.execute(statement, values)
            self._connection.commit()
            return cursor
        except:
            print("\nLast Query:", cursor.query, "\n")
            self._connection.rollback()
            raise
            
    def iterator(self, cursor):
        """
        @description Alternative to having the `x = cursor.fetchone()` ... 
        `while x is not None` every time that we're iterating through DB results

        @yields a row fetched from the cursor.
        """
        warn(
            "Unlike sqlite, postgres provides an iterable cursor. No need to call me", 
            DeprecationWarning
        )
        row = cursor.fetchone()
        while row is not None:
            yield row
            row = cursor.fetchone()
