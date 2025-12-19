import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ DB 준비 완료!")

if __name__ == "__main__":
    init_db()
