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
        self.__connection = connect(config.DATABASE_URL)
        self.launch()
        atexit.register(self.disconnect)

    def disconnect(self):
        """
        Close the connection to the database. Should be called before exiting 
        the script.
        """
        self.__connection.close()
    
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
            "status VARCHAR(255), deadline DATE, recent_updater_id INT);"
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
        cursor = self.__connection.cursor(cursor_factory=cursor_factory)
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
            self.__connection.commit()
            return cursor
        except:
            print("\nLast Query:", cursor.query, "\n")
            self.__connection.rollback()
            raise

    def execute_many(self, sql_query, values, dynamic_table_or_column_names=None, 
                     cursor_factory=extras.DictCursor):
        """
        Execute many related SQL queries, e.g. update several rows of a table.

        @param str `sql_query`: the query to execute. It must contain a single 
        `%s` placeholder

        @param List[List] `values`: Each item should be a value that can be 
        substituted when composing a SQL query

        """
        if dynamic_table_or_column_names is not None:
            sql_query = sql.SQL(sql_query).format(*[
                sql.Identifier(s) for s in dynamic_table_or_column_names
            ])
        cursor = self.__connection.cursor(cursor_factory=cursor_factory)
        try:
            extras.execute_values(cursor, sql_query, values)
            self.__connection.commit()
            return cursor
        except:
            print("\nLast Query:", cursor.query, "\n")
            self.__connection.rollback()
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
