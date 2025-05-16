import sqlite3

def check_and_fix_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()

        # Get table info
        cursor.execute("PRAGMA table_info(work_entry)")
        columns = cursor.fetchall()
        print("Current table structure:")
        for col in columns:
            print(col)

        # Drop and recreate the table with correct structure
        cursor.execute('DROP TABLE IF EXISTS work_entry')
        
        cursor.execute('''
        CREATE TABLE work_entry (
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
            overtime_hours FLOAT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        ''')

        # Commit changes
        conn.commit()
        print("\nDatabase structure has been updated successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    check_and_fix_database() 