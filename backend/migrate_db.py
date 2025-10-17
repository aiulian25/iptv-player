import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "./data/database.db")

def migrate():
    """Add missing columns to existing database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if channel_count column exists
        cursor.execute("PRAGMA table_info(playlists)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'channel_count' not in columns:
            print("Adding channel_count column...")
            cursor.execute("ALTER TABLE playlists ADD COLUMN channel_count INTEGER DEFAULT 0")
            conn.commit()
            print("✓ Added channel_count column")
        
        print("✓ Database migration complete")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
