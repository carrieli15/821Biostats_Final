"""Module for managing student information stored in a SQLite database.

This module provides classes and functions for interacting with student data
stored in a SQLite database. The main classes included in this module are:

- `StudentManager`: A class for managing student information in the database,
  including methods for creating tables, parsing data from TSV files,
  inserting,updating, deleting, exporting student records, etc.

- `StudentList`: A class representing a list of all students in the database,
  providing methods to retrieve specific attributes of a student.

"""

import sqlite3
from datetime import datetime
from typing import Any


class StudentManager:
    """A class to manage student information stored in a SQLite database."""

    def __init__(self, db_path: str) -> None:
        """Initializes the StudentManager object.

        Args:
            db_path (str): The file path to the SQLite database.
        """
        self.db_path = db_path
        self.create_tables()

    def connect(self) -> sqlite3.Connection:
        """Establishes a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.
        """
        return sqlite3.connect(self.db_path)

    def create_tables(self) -> None:
        """Creates the tables in the database if they do not exist."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student (
                    ID TEXT PRIMARY KEY,
                    Name TEXT,
                    Gender TEXT,
                    Enroll_Date TEXT,
                    English TEXT,
                    Math TEXT,
                    History TEXT,
                    Science TEXT,
                    Arts TEXT
                )
            """)
            conn.commit()

    def parse_data(self, student_filename: str) -> None:
        """Parses data from TSV files into the database.

        Args:
            student_filename (str): The file path of the TSV file containing
            student data.
        """
        with self.connect() as conn, open(
            student_filename, encoding="utf-8"
        ) as student_file:
            cursor = conn.cursor()

            # Process student data
            headers = student_file.readline().strip().split("\t")
            for line in student_file:
                values = line.strip().split("\t")
                record = dict(zip(headers, values))
                cursor.execute(
                    """INSERT OR IGNORE INTO student (
                        ID, Name, Gender, 
                        Enroll_Date, English, Math, 
                        History, Science, Arts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record["ID"],
                        record["Name"],
                        record["Gender"],
                        record["Enroll_Date"],
                        record["English"],
                        record["Math"],
                        record["History"],
                        record["Science"],
                        record["Arts"],
                    ),
                )
            conn.commit()

    def insert_student(self, student_data: dict) -> None:
        """Inserts a new student into the database.

        Args:
            student_data (dict): Dictionary containing student information.
                Keys: 'ID', 'Name', 'Gender', 'Enroll_Date', 'English', 'Math',
                'History', 'Science', 'Arts'.

        Raises:
            ValueError: If any value in student_data has an invalid data type.
        """
        # Define the expected data types for each field

        expected_types = {
            "ID": str,
            "Name": str,
            "Gender": str,
            "Enroll_Date": str,
            "English": str,
            "Math": str,
            "History": str,
            "Science": str,
            "Arts": str,
        }

        # Validate the data types of the values
        for key, value in student_data.items():
            if not isinstance(value, expected_types[key]):
                raise ValueError(
                    f"Invalid data type for {key}: expected"
                    f"{expected_types[key]}, got {type(value)}"
                )

            # If all data types are valid, insert the student into the database
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO student (ID, Name, Gender, Enroll_Date,"
                    "English, Math, History, Science, Arts) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        student_data.get("ID"),
                        student_data.get("Name"),
                        student_data.get("Gender"),
                        student_data.get("Enroll_Date"),
                        student_data.get("English"),
                        student_data.get("Math"),
                        student_data.get("History"),
                        student_data.get("Science"),
                        student_data.get("Arts"),
                    ),
                )
                conn.commit()

    def delete_student(self, student_id: str) -> bool:
        """Deletes a student from the database based on their ID.

        Args:
            student_id (str): The ID of the student to be deleted.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            # First, check if the student exists
            cursor.execute(
                "SELECT ID FROM student WHERE ID = ?", (student_id,)
            )
            if cursor.fetchone() is None:
                return False

            try:
                cursor.execute(
                    "DELETE FROM student WHERE ID = ?", (student_id,)
                )
                conn.commit()
                # Verify that the student was deleted
                cursor.execute(
                    "SELECT ID FROM student WHERE ID = ?", (student_id,)
                )
                return cursor.fetchone() is None
            except sqlite3.DatabaseError:
                return False

    def check_student(self, student_id: str) -> bool:
        """Checks if a student with the given ID exists in the database.

        Args:
            student_id (str): The ID of the student to check.

        Returns:
            bool: True if the student exists, False otherwise.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID FROM student WHERE ID = ?", (student_id,)
            )
            return cursor.fetchone() is not None

    def update_student(self, student_id: str, **updates: Any) -> bool:
        """Updates attributes for a specific student in the database.

        Args:
            student_id (str): The ID of the student to update.
            updates (dict[str, Any]): A dictionary of attribute-value pairs to
            update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if not student_id:
            return False

        with self.connect() as conn:
            student = StudentList(conn, student_id)
            if not student.student_id:
                return False

            # Prepare current values; ensure attribute names match
            current_values = {
                key: str(getattr(student, f"student_{key}", None))
                for key in updates
            }

            # Check if any updates are actually needed
            if all(
                current_values.get(key) == str(updates[key]) for key in updates
            ):
                return False

            # Proceed with the update if necessary
            set_clause = ", ".join([f"{key} = ?" for key in updates])
            values = list(updates.values())
            values.append(student_id)
            sql_query = f"UPDATE student SET {set_clause} WHERE ID = ?"
            cursor = conn.cursor()
            cursor.execute(sql_query, values)
            conn.commit()
            return True

    def export_data(self, filename: str = "new_student.tsv") -> None:
        """Exports student data from the database to a TSV file.

        Args:
            filename (str): The file path to save the exported data.
                Defaults to "new_student.tsv".
        """
        with self.connect() as conn, open(
            filename, "w", newline="", encoding="utf-8"
        ) as file:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student")
            # Write header
            file.write(
                "\t".join(
                    [description[0] for description in cursor.description]
                )
                + "\n"
            )
            # Write data
            for row in cursor.fetchall():
                file.write("\t".join(str(col) for col in row) + "\n")

        print("Data exported successfully to:", filename)


class StudentList:
    """Represents a list for all students."""

    def __init__(
        self, connection: sqlite3.Connection, students_id: str
    ) -> None:
        """Initializes the StudentList object.

        Args:
            connection: The connection to the SQLite database.
            students_id (int): The ID of the students.
        """
        self.students_id = students_id
        self.connection = connection

    def _getattribute_(self, attribute: str) -> Any:
        """Retrieve a specific attribute from the database for the student.

        Args:
            attribute (str): The attribute to retrieve from the database.

        Returns:
            Any: The value of the requested attribute.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            f"SELECT {attribute} FROM student WHERE ID = ?",
            (self.students_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None

    @property
    def student_id(self) -> Any:
        """Get the student's ID."""
        return self._getattribute_("ID")

    @property
    def student_name(self) -> Any:
        """Get the student's name."""
        return self._getattribute_("Name")

    @property
    def student_gender(self) -> Any:
        """Get the student's gender."""
        return self._getattribute_("Gender")

    @property
    def student_enrollment(self) -> Any:
        """Get the student's enrollment date."""
        datetime_string = self._getattribute_("Enroll_Date")
        return (
            datetime.strptime(datetime_string, "%m-%d-%Y")
            if datetime_string
            else None
        )

    @property
    def student_english(self) -> Any:
        """Get the student's English grade."""
        return self._getattribute_("English")

    @property
    def student_math(self) -> Any:
        """Get the student's Math grade."""
        return self._getattribute_("Math")

    @property
    def student_history(self) -> Any:
        """Get the student's History grade."""
        return self._getattribute_("History")

    @property
    def student_science(self) -> Any:
        """Get the student's Science grade."""
        return self._getattribute_("Science")

    @property
    def student_arts(self) -> Any:
        """Get the student's Arts grade."""
        return self._getattribute_("Arts")


# this class is going to calculate max, min and mean for students' grade
# class Grades:
#     """Strat from here."""


# # just for test
# def main():
#     # Path to the SQLite database file
#     db_path = "student.db"

#     # Initialize the StudentManager
#     manager = StudentManager(db_path)

#     # Parse student data from a TSV file into the database
#     student_filename = "student.tsv"
#     manager.parse_data(student_filename)
#     student_id = "58452"

#     # Check if the student exists using the StudentList class
#     with manager.connect() as conn:
#         student = StudentList(conn, student_id)
#         if student.student_id:
#             print(
#                 f"Student {student_id} found. Current English grade:"
#                 f" {student.student_english}"
#             )
#         else:
#             print(f"Student {student_id} not found. Check the data file.")
#             return  # Exit if student not found to avoid further errors

#     # Update the student's English grade
#     new_english_grade = 95  # New grade to update
#     print("Updating the student's English grade...")
#     if manager.update_student(student_id, English=new_english_grade):
#         print("Update successful!")
#     else:
#         print("Update failed.")

#     # Re-check the updated details
#     with manager.connect() as conn:
#         student = StudentList(conn, student_id)
#         print(
#             f"After update, English grade for student {student_id}:"
#             f"{student.student_english}"
#         )
#     # demonstrate deletion
#     print("Deleting the student for cleanup...")
#     if manager.delete_student(student_id):
#         print(f"Student {student_id} successfully deleted.")
#     else:
#         print("Failed to delete the student.")
#     # Export data to a TSV file
#     export_filename = "new_student.tsv"
#     manager.export_data(export_filename)


# if __name__ == "__main__":
#     main()
