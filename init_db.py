import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect('leaderboard.db')
cursor = conn.cursor()

# Create a leaderboard table
cursor.execute('''
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INTEGER NOT NULL
)
''')

conn.commit()
conn.close()

print("Database initialized.")
