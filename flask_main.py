"""A Flask web application for managing student data.

This script initializes a Flask application to manage student records stored
in a SQLite database. It provides web routes for displaying student
information, adding new student records, updating existing records,
and deleting students. The application uses templates for rendering HTML
responses.

Modules:
- sqlite3: For database operations.
- Flask: For creating and running the web application.
- render_template, request: From Flask, for rendering templates and handling
requests.
- Grades, StudentManager: Custom modules for handling student data operations
and calculations.
"""

import sqlite3

from flask import Flask, render_template, request
from student import Grades, StudentManager

app = Flask(__name__, template_folder="frontend")

database_path = "check_student.db"
student_manager = StudentManager(database_path)
student_filename = "student.tsv"
student_manager.parse_data(student_filename)


@app.route("/")
def home():
    """Render the home page."""
    return render_template("home.html")


@app.route("/student", methods=["POST"])
def show_student():
    """Display student information or an error message."""
    student_id = request.form.get("student_id")
    with student_manager.connect() as conn:
        student_info = student_manager.get_student_by_id(student_id)
        if student_info:
            scores = {
                "math_max": Grades.get_max_score(conn, "Math"),
                "math_min": Grades.get_min_score(conn, "Math"),
                "math_avg": Grades.get_avg_score(conn, "Math"),
            }
            scores = {
                "English_max": Grades.get_max_score(conn, "English"),
                "English_min": Grades.get_min_score(conn, "English"),
                "English_avg": Grades.get_avg_score(conn, "English"),
                "math_max": Grades.get_max_score(conn, "Math"),
                "math_min": Grades.get_min_score(conn, "Math"),
                "math_avg": Grades.get_avg_score(conn, "Math"),
                "History_max": Grades.get_max_score(conn, "History"),
                "History_min": Grades.get_min_score(conn, "History"),
                "History_avg": Grades.get_avg_score(conn, "History"),
                "Science_max": Grades.get_max_score(conn, "Science"),
                "Science_min": Grades.get_min_score(conn, "Science"),
                "Science_avg": Grades.get_avg_score(conn, "Science"),
                "Arts_max": Grades.get_max_score(conn, "Arts"),
                "Arts_min": Grades.get_min_score(conn, "Arts"),
                "Arts_avg": Grades.get_avg_score(conn, "Arts"),
            }
        else:
            return render_template(
                "home.html", error_message="Student not found"
            )

    return render_template(
        "home.html", student_info=student_info, scores=scores
    )


@app.route("/add_student", methods=["POST"])
def add_student():
    """Add a new student to the database and display result."""
    student_data = {
        "ID": request.form.get("ID"),
        "Name": request.form.get("Name"),
        "Gender": request.form.get("Gender"),
        "Enroll_Date": request.form.get("Enroll_Date"),
        "English": request.form.get("English"),
        "Math": request.form.get("Math"),
        "History": request.form.get("History"),
        "Science": request.form.get("Science"),
        "Arts": request.form.get("Arts"),
    }
    try:
        student_manager.insert_student(student_data)
        message = "Successfully Submit!"
        return render_template("home.html", message=message)
    except ValueError as ve:
        error_message = str(ve)
        return render_template("home.html", error_message=error_message)
    except sqlite3.IntegrityError as ie:
        error_message = str(ie)
        return render_template("home.html", error_message=error_message)


@app.route("/update_student/<student_id>", methods=["POST"])
def update_student(student_id):
    """Update specific student data and display the result."""
    field = request.form.get("field")
    new_value = request.form.get("new_value")
    updates = {field: new_value}
    if student_manager.update_student(student_id, **updates):
        print("Update successful!")
        error_message = "Update successful!"
    else:
        print("Update failed.")
        error_message = "Update failed."
    return render_template("home.html", error_message=error_message)


@app.route("/delete_student/<student_id>", methods=["GET"])
def delete_student(student_id):
    """Delete a student from the database and display the result."""
    if student_manager.delete_student(student_id):
        print(f"Student {student_id} successfully deleted.")
        error_message = f"Student {student_id} successfully deleted."
    else:
        print("Failed to delete the student.")
        error_message = "Failed to delete the student."
    return render_template("home.html", error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)
