#!/usr/bin/env python

import os
fileDir  = os.path.dirname(os.path.realpath('__file__'))
FILENAME = os.path.join(fileDir, '../footprints.json')
DBNAME   = os.path.join(fileDir, '../footprints.sqlite')
import sqlite3
import json

def main():
    """
    Loads footprints.json into a single table in SQLite, only if
    the table already does not exist.
    """

    print("Loading input data from %s" % FILENAME)
    input_data = None
    with open(FILENAME) as json_data:
        input_data = json.loads(json_data.read())

    print("Opening connection to %s" % DBNAME)
    conn = sqlite3.connect(DBNAME,timeout=10, isolation_level=None, check_same_thread = False)
    cursor = conn.cursor()

    create_query = '''
        CREATE TABLE IF NOT EXISTS footprints
        (
            id INTEGER,
            description TEXT,
            status TEXT,
            status2 TEXT,
            created TEXT,
            last_updated TEXT,
            created_updated_diff REAL,
            interactions INTEGER,
            issuetype TEXT,
            first_name TEXT,
            last_name TEXT,
            parties TEXT
        )
    '''
    # Create table
    print("Creating footprints table...")
    cursor.execute(create_query)

    for entry in input_data:
        # Insert data
        print("Inserting entry %s" % entry['id'])
        row = (
                entry['id'],
                entry['description'],
                entry['status'],
                entry['status2'],
                entry['created'],
                entry['last_updated'],
                entry['created_updated_diff'],
                entry['interactions'],
                entry['issuetype'],
                entry['first_name'],
                entry['last_name'],
                entry['parties']
            )
        cursor.executemany(
            'INSERT INTO footprints VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
            [row]
        )

    cursor.close()
    conn.close()

    print("Done! Bye!!!")

if __name__ == '__main__':
    main()