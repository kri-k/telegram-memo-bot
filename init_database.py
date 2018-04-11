import sqlite3

conn = sqlite3.connect("locations.db")
cursor = conn.cursor()

print('Opened database locations.db successfully')

cursor.execute('''CREATE TABLE Locations (
    ChatId INTEGER,
    Latitude TEXT,
    Longitude TEXT
);''')

print("Table 'Locations' was created")

conn.close()


conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

print('Opened database tasks.db successfully')

cursor.execute('''CREATE TABLE Tasks (
    Id INTEGER,
    ChatId INTEGER,
    NoteText TEXT,
    UTCTimestamp INTEGER
);''')

print("Table 'Tasks' was created")

conn.close()