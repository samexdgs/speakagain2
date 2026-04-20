import sqlite3
from datetime import datetime

DB_NAME = "speakagain.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_username TEXT,
        action TEXT,
        concern INTEGER,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_activity(patient_username, action, concern=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO activity (patient_username, action, concern, timestamp)
    VALUES (?, ?, ?, ?)
    """, (
        patient_username,
        action,
        int(concern),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def load_activity(patient_username, limit=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT action, concern, timestamp
    FROM activity
    WHERE patient_username=?
    ORDER BY id DESC
    LIMIT ?
    """, (patient_username, limit))

    rows = c.fetchall()
    conn.close()

    return [
        {"action": r[0], "concern": bool(r[1]), "time": r[2]}
        for r in rows
    ]
