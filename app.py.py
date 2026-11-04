"""Task 1 - Flask REST API with SQLite (Student Management)
Run:  python app.py      ->  http://127.0.0.1:5000
"""
import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS students (
                   student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name       TEXT NOT NULL,
                   department TEXT NOT NULL,
                   email      TEXT NOT NULL UNIQUE
               )"""
        )


def validate(data):
    """Return an error message if data is invalid, else None."""
    if not isinstance(data, dict):
        return "Request body must be JSON"
    for field in ("name", "department", "email"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"'{field}' is required"
    if "@" not in data["email"]:
        return "'email' is not valid"
    return None


@app.get("/students")
def get_students():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.get("/students/<int:student_id>")
def get_student(student_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(dict(row)), 200


@app.post("/students")
def add_student():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO students (name, department, email) VALUES (?, ?, ?)",
                (data["name"].strip(), data["department"].strip(), data["email"].strip()),
            )
            new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "A student with this email already exists"}), 409
    return jsonify({"message": "Student added", "student_id": new_id}), 201


@app.put("/students/<int:student_id>")
def update_student(student_id):
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "UPDATE students SET name = ?, department = ?, email = ? WHERE student_id = ?",
                (data["name"].strip(), data["department"].strip(),
                 data["email"].strip(), student_id),
            )
            if cur.rowcount == 0:
                return jsonify({"error": "Student not found"}), 404
    except sqlite3.IntegrityError:
        return jsonify({"error": "A student with this email already exists"}), 409
    return jsonify({"message": "Student updated"}), 200


@app.delete("/students/<int:student_id>")
def delete_student(student_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404
    return jsonify({"message": "Student deleted"}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
