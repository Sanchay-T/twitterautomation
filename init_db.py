import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('tweets.db')
    c = conn.cursor()
    
    # Drop existing table if you want to start fresh
    c.execute('DROP TABLE IF EXISTS tweets')
    
    # Create tweets table with all necessary columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet TEXT NOT NULL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_time TIMESTAMP
        )
    ''')
    
    # Insert sample data
    current_time = datetime.now()
    sample_tweets = [
        ("This is sample tweet 1", "approved", current_time + timedelta(minutes=18)),
        ("This is sample tweet 2", "approved", current_time + timedelta(minutes=36)),
        ("This is sample tweet 3", None, None),  # Pending review
        ("This is sample tweet 4", None, None),  # Pending review
    ]
    
    c.executemany('''
        INSERT INTO tweets (tweet, status, scheduled_time)
        VALUES (?, ?, ?)
    ''', sample_tweets)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data")

if __name__ == "__main__":
    init_db()
