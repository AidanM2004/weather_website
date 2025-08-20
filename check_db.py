import sqlite3

conn = sqlite3.connect('leaderboard.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM leaderboard ORDER BY score DESC")
rows = cursor.fetchall()

print("Leaderboard entries:")
for row in rows:
    print(row)

conn.close()
