# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect("locations.db", check_same_thread=False)
cursor = conn.cursor()


def insert(chat_id, geopos):
    sql = '''INSERT INTO Locations (ChatId, Latitude, Longitude)
    VALUES (?, ?, ?)'''
    cursor.execute(sql, (chat_id, *geopos))
    conn.commit()


def update(chat_id, geopos):
    sql = '''UPDATE Locations SET
    Latitude = ?,
    Longitude = ?
    WHERE ChatId = ?'''
    cursor.execute(sql, (*geopos, chat_id))
    conn.commit()


def get(chat_id):
    sql = 'SELECT Latitude, Longitude FROM Locations WHERE ChatId = ?'
    cursor.execute(sql, (chat_id,))
    return cursor.fetchone()


if __name__ == '__main__':
    pass