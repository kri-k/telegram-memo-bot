# -*- coding: utf-8 -*-

import sqlite3

conn_loc = sqlite3.connect("locations.db")
conn_tasks = sqlite3.connect("tasks.db")


def get(cursor, tbl):
    sql = 'SELECT * FROM %s'
    cursor.execute(sql % tbl)
    return cursor.fetchall()


if __name__ == '__main__':
    print('Locations:')
    print(*get(conn_loc.cursor(), 'Locations'), sep='\n')
    conn_loc.close()
    print('Tasks')
    print(*get(conn_tasks.cursor(), 'Tasks'), sep='\n')
    conn_tasks.close()