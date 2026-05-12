# visitor_db.py

import sqlite3
from datetime import datetime

DB_NAME = "visitor_logs.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visitors (
        name TEXT PRIMARY KEY,
        visit_count INTEGER,
        last_visit TEXT,
        wrong_attempts INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def update_visitor(name, wrong_otp=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT visit_count, wrong_attempts FROM visitors WHERE name=?", (name,))
    result = cursor.fetchone()

    if result:
        visit_count, wrong_attempts = result
        visit_count += 1

        if wrong_otp:
            wrong_attempts += 1

        cursor.execute("""
            UPDATE visitors 
            SET visit_count=?, last_visit=?, wrong_attempts=? 
            WHERE name=?
        """, (visit_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), wrong_attempts, name))

    else:
        visit_count = 1
        wrong_attempts = 1 if wrong_otp else 0

        cursor.execute("""
            INSERT INTO visitors (name, visit_count, last_visit, wrong_attempts)
            VALUES (?, ?, ?, ?)
        """, (name, visit_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), wrong_attempts))

    conn.commit()
    conn.close()

    return visit_count, wrong_attempts