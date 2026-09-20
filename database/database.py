import sqlite3
import os


# ==========================================
# DATABASE PATH
# ==========================================

DATABASE_FOLDER = "database"

DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    "resume_analyzer.db"
)


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    os.makedirs(
        DATABASE_FOLDER,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            resume_name TEXT,

            overall_score REAL,

            skill_score REAL,

            nlp_score REAL,

            matched_skills TEXT,

            missing_skills TEXT,

            analyzed_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """)

    connection.commit()

    connection.close()


# ==========================================
# SAVE ANALYSIS
# ==========================================

def save_analysis(

    resume_name,
    overall_score,
    skill_score,
    nlp_score,
    matched_skills,
    missing_skills

):

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO analyses (

            resume_name,
            overall_score,
            skill_score,
            nlp_score,
            matched_skills,
            missing_skills

        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        resume_name,

        overall_score,

        skill_score,

        nlp_score,

        ", ".join(matched_skills),

        ", ".join(missing_skills)

    ))

    connection.commit()

    connection.close()


# ==========================================
# GET ANALYSIS HISTORY
# ==========================================

def get_analysis_history():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *

        FROM analyses

        ORDER BY analyzed_at DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# ==========================================
# INITIALIZE DATABASE
# ==========================================

create_database()