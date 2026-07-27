import sqlite3


DATABASE = "fittrack.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE / UPGRADE DATABASE
# =========================================================

def init_db():

    connection = get_db_connection()

    cursor = connection.cursor()


    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)


    # =====================================================
    # GOALS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            goal TEXT NOT NULL,

            completed INTEGER NOT NULL DEFAULT 0,

            date TEXT NOT NULL,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)


    # =====================================================
    # CHECK IF GOALS NEED user_id
    # =====================================================

    cursor.execute("""
        PRAGMA table_info(goals)
    """)

    goal_columns = [
        column["name"]
        for column in cursor.fetchall()
    ]


    if "user_id" not in goal_columns:

        cursor.execute("""
            ALTER TABLE goals
            ADD COLUMN user_id INTEGER
        """)


    # =====================================================
    # WORKOUTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            exercise TEXT NOT NULL,

            sets INTEGER NOT NULL,

            reps INTEGER NOT NULL,

            category TEXT NOT NULL,

            completed INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)


    # =====================================================
    # CHECK IF WORKOUTS NEED user_id
    # =====================================================

    cursor.execute("""
        PRAGMA table_info(workouts)
    """)

    workout_columns = [
        column["name"]
        for column in cursor.fetchall()
    ]


    if "user_id" not in workout_columns:

        cursor.execute("""
            ALTER TABLE workouts
            ADD COLUMN user_id INTEGER
        """)


    # =====================================================
    # SAVE CHANGES
    # =====================================================

    connection.commit()

    connection.close()


# =========================================================
# RUN DATABASE SETUP
# =========================================================

if __name__ == "__main__":

    init_db()

    print(
        "FitTrack database initialized successfully!"
    )