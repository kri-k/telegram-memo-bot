# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()


def insert(chat_id, task):
    sql = '''INSERT INTO Tasks (Id, ChatId, NoteText, UTCTimestamp)
    VALUES (?, ?, ?, ?)'''
    cursor.execute(sql, (task.id, chat_id, task.text, task.time))
    conn.commit()


def delete(id, chat_id):
    sql = 'DELETE FROM Tasks WHERE Id = ? AND ChatId = ?'
    cursor.execute(sql, (id, chat_id))
    conn.commit()


def get_all_in_chat(chat_id):
    sql = 'SELECT * FROM Tasks WHERE ChatId = ?'
    cursor.execute(sql, (chat_id,))
    return cursor.fetchall()


def get_all():
    sql = 'SELECT * FROM Tasks'
    cursor.execute(sql)
    return cursor.fetchall()


if __name__ == '__main__':
    pass