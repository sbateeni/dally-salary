from app import db
import sqlite3

def migrate_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()

        # Create a new table with the updated schema
        cursor.execute('''
        CREATE TABLE work_entry_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            day VARCHAR(20) NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            total_hours FLOAT NOT NULL,
            pay FLOAT NOT NULL,
            note VARCHAR(200),
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        ''')

        # Copy data from the old table to the new one
        cursor.execute('''
        INSERT INTO work_entry_new (
            id, date, day, start_time, end_time, 
            total_hours, pay, note, user_id, created_at
        )
        SELECT 
            id, date, day, start_time, end_time, 
            total_hours, pay, note, user_id, created_at
        FROM work_entry
        ''')

        # Drop the old table
        cursor.execute('DROP TABLE work_entry')

        # Rename the new table to the original name
        cursor.execute('ALTER TABLE work_entry_new RENAME TO work_entry')

        # Commit the changes
        conn.commit()
        print("Database migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database() 