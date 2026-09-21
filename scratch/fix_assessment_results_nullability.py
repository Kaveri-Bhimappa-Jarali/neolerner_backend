import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'literacy.db'))
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Current table definition:")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='assessment_results'")
row = cursor.fetchone()
print(row[0] if row else "Table not found")

# Migrate table in SQLite
cursor.execute("PRAGMA foreign_keys=off;")
cursor.execute("BEGIN TRANSACTION;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assessment_results_new (
    id CHAR(32) NOT NULL PRIMARY KEY,
    learner_id CHAR(32) NOT NULL,
    assessment_id CHAR(32),
    score FLOAT NOT NULL,
    max_score FLOAT,
    passed BOOLEAN,
    completed_at DATETIME,
    cefr_level VARCHAR,
    skill_breakdown TEXT,
    strengths TEXT,
    weak_areas TEXT,
    FOREIGN KEY(learner_id) REFERENCES learners (id),
    FOREIGN KEY(assessment_id) REFERENCES assessments (id)
);
""")

cursor.execute("""
INSERT INTO assessment_results_new (
    id, learner_id, assessment_id, score, max_score, passed, completed_at, cefr_level, skill_breakdown, strengths, weak_areas
)
SELECT id, learner_id, assessment_id, score, max_score, passed, completed_at, cefr_level, skill_breakdown, strengths, weak_areas
FROM assessment_results;
""")

cursor.execute("DROP TABLE assessment_results;")
cursor.execute("ALTER TABLE assessment_results_new RENAME TO assessment_results;")

cursor.execute("COMMIT;")
cursor.execute("PRAGMA foreign_keys=on;")

print("\nUpdated table definition:")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='assessment_results'")
print(cursor.fetchone()[0])

conn.close()
print("Migration completed successfully!")
