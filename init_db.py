from db import get_connection

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id SERIAL PRIMARY KEY,
        task TEXT NOT NULL,
        status INTEGER DEFAULT 0,
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments(
        id SERIAL PRIMARY KEY,
        assignment_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        due_date DATE NOT NULL,
        priority INTEGER NOT NULL,
        status INTEGER DEFAULT 0,
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semesters(
        id SERIAL PRIMARY KEY,
        semester_no INTEGER NOT NULL,
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id SERIAL PRIMARY KEY,
        subject_name TEXT NOT NULL,
        credits INTEGER NOT NULL,
        grade INTEGER NOT NULL,
        semester_id INTEGER NOT NULL REFERENCES semesters(id),
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable(
        id SERIAL PRIMARY KEY,
        day INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        semester_id INTEGER NOT NULL REFERENCES semesters(id),
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id SERIAL PRIMARY KEY,
        timetable_id INTEGER NOT NULL REFERENCES timetable(id),
        date DATE NOT NULL,
        status INTEGER NOT NULL,
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productivity_history(
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        score REAL,
        record_date DATE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER,
        subject TEXT,
        extracted_text TEXT,
        summary_json TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_reports(
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        report_type TEXT NOT NULL,
        report_json TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_plans(
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        plan_json TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()