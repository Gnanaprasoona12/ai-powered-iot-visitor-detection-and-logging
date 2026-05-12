import sqlite3

# Create database file
conn = sqlite3.connect("visitor_logs.db")

# Create table
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    person_type TEXT,
    status TEXT,
    room TEXT,
    image_path TEXT,
    risk_score INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("Database created successfully")