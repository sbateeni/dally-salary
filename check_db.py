import sqlite3

def check_and_fix_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()

        # Drop existing tables
        cursor.execute('DROP TABLE IF EXISTS work_entry')
        cursor.execute('DROP TABLE IF EXISTS user')
        
        # Create work_entry table
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            overtime_hours FLOAT DEFAULT 0
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