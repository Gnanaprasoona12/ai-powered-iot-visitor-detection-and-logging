import sqlite3
import os

DB_PATH = "visitor_logs.db"

def run_migration():
    if not os.path.exists(DB_PATH):
        print("DB does not exist yet.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get last 2 IDs and delete them
    print("Deleting last 2 entries...")
    cursor.execute("SELECT id FROM logs ORDER BY id DESC LIMIT 2")
    rows = cursor.fetchall()
    for row in rows:
        _id = row[0]
        cursor.execute("DELETE FROM logs WHERE id=?", (_id,))
        print(f"Deleted row id: {_id}")

    # Add risk_score column
    print("Adding risk_score column if not exists...")
    try:
        cursor.execute("ALTER TABLE logs ADD COLUMN risk_score INTEGER DEFAULT 0")
        print("Added risk_score column successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("risk_score column already exists.")
        else:
            print("Already existed or other error:", e)

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
