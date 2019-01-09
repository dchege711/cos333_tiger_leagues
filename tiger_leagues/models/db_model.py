"""
db.py

A wrapper around the database used by the 'Tiger Leagues' app

"""

from sys import stderr
from warnings import warn
import atexit
from psycopg2 import connect, extras, sql
from . import config

class Database:
    """
    A wrapper around the database used by the 'Tiger Leagues' app
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
            "user_id SERIAL PRIMARY KEY, name VARCHAR(255), net_id VARCHAR(255) UNIQUE, "
            "email VARCHAR(255), phone_num VARCHAR(255), room VARCHAR(255), "
            "league_ids TEXT);"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS match_info ("
            "match_id SERIAL PRIMARY KEY, user_1_id INT, user_2_id INT, league_id INT, "
            "division_id INT, score_user_1 INT, score_user_2 INT, "
            "status VARCHAR(255), deadline DATE, recent_updater_id INT);"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS league_info ("
            "league_id SERIAL PRIMARY KEY, league_name VARCHAR(255), "
            "description TEXT, points_per_win INT NOT NULL, points_per_draw INT NOT NULL, "
            "points_per_loss INT, registration_deadline DATE, max_num_players INT, "
            "creator_user_id INT NOT NULL, num_games_per_period INT NOT NULL, length_period_in_days INT NOT NULL, "
            "additional_questions TEXT, league_status VARCHAR(255));"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS league_standings ("
            "standing_id SERIAL PRIMARY KEY, league_id INT, division_id INT, "
            "user_id INT, wins INT, losses INT, draws INT, games_played INT, "
            "goals_for INT, goals_allowed INT, goal_diff INT, points INT, "
            "rank INT, rank_delta INT);"
        ))

        self.execute((
            "CREATE TABLE IF NOT EXISTS notifications ("
            "notification_id SERIAL PRIMARY KEY, user_id INT, league_id INT, "
            "notification_status VARCHAR DEFAULT 'delivered', notification_text TEXT, "
            "created_at TIMESTAMPTZ DEFAULT NOW());"
        ))

    def execute(self, statement, values=None, dynamic_table_or_column_names=None, 
                cursor_factory=extras.DictCursor):
        """
        :param statement: str

        The SQL query to run.

        :kwarg values: list

        Values that the query's placeholders should be replaced with

        :kwarg dynamic_table_or_column_names: list

        Names of tables/columns that should be substituted into the SQL statement

        :kwarg cursor_factory: psycopg2.extensions.cursor

        The type of object that should be generated by calls to the ``cursor()`` 
        method.

        :return: ``cursor``
        
        The cursor after after executing the SQL query
        
        :raise: ``psycopg2.errors``
        
        If the SQL transaction fails, the transaction is rolled back. The most 
        recently executed query is printed to ``sys.stderr``. The error is then 
        raised.

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
            print("\nLast Query:", cursor.query, "\n", file=stderr)
            self.__connection.rollback()
            raise

    def execute_many(self, sql_query, values, dynamic_table_or_column_names=None, 
                     cursor_factory=extras.DictCursor):
        """
        Execute many related SQL queries, e.g. update several rows of a table.

        :param sql_query: str

        The SQL query to run. It must contain a single `%s` placeholder

        :kwarg values: iterable

        Each item should be a value that can be substituted when composing a 
        SQL query

        :kwarg dynamic_table_or_column_names: list

        Names of tables/columns that should be substituted into the SQL statement

        :kwarg cursor_factory: psycopg2.extensions.cursor

        The type of object that should be generated by calls to the ``cursor()`` 
        method.

        :return: ``cursor``
        
        The cursor after after executing the SQL query
        
        :raise: ``psycopg2.errors`` 
        
        If the SQL transaction fails, the transaction is rolled back. The most 
        recently executed query is printed to ``sys.stderr``. The error is then 
        raised.

        """
        if dynamic_table_or_column_names is not None:
            sql_query = sql.SQL(sql_query).format(*[
                sql.Identifier(s) for s in dynamic_table_or_column_names
            ])

        cursor = self.__connection.cursor(cursor_factory=cursor_factory)
        if values and isinstance(values[0], dict):
            template = "({})".format(", ".join(["%({})s".format(x) for x in values[0].keys()]))
        else:
            template = None

        try:
            extras.execute_values(cursor, sql_query, values, template=template)
            self.__connection.commit()
            return cursor
        except:
            print("\nLast Query:", cursor.query, "\n", file=stderr)
            self.__connection.rollback()
            raise
            
    def iterator(self, cursor):
        """
        An alternative to having the ``x = cursor.fetchone()` ... 
        `while x is not None`` dance when iterating through cursor's results.

        :param cursor: psycopg2.cursor
        
        The cursor after after executing the SQL query

        :yield: ``Row``
        
        A row fetched from the cursor.

        :warn: ``DepracationWarning``

        Unlike sqlite3, psycopg2 provides an iterable cursor, so this method 
        is unnecessary baggage.
        """
        warn(
            "Unlike sqlite3, postgres provides an iterable cursor. No need to call me", 
            DeprecationWarning
        )
        row = cursor.fetchone()
        while row is not None:
            yield row
            row = cursor.fetchone()
