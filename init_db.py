import sqlite3

conn = sqlite3.connect('leaderboard.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INTEGER NOT NULL
)
''')

conn.commit()
conn.close()

print("Leaderboard table ready.")
