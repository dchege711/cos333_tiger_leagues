"""
clean_database.py

Utility script for deleting all the tables. Useful when the schema for the table 
changes.

"""

import sys
sys.path.insert(0, "..")

from tiger_leagues import db as database

db = database.Database()
cursor = db.execute((
    "SELECT tablename FROM pg_catalog.pg_tables "
    "WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"
))

table_names = [row["tablename"] for row in cursor]

cursor = db.execute(
    "DROP TABLE {}".format(", ".join(["{}" for _ in table_names])),
    dynamic_table_or_column_names=table_names
)

print("Dropped all the tables")
