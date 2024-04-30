"""Tests for the student management system.

These tests cover the functionality of the StudentManager and StudentList
classes,which are responsible for managing student data stored in a SQLite
database.

Attributes:
    student_manager (pytest.fixture): Fixture providing an instance of
    StudentManager with a fresh database for testing.
    load_data (pytest.fixture): Fixture that loads test data into the fresh
    database. It uses the student_manager fixture.
    tmp_path (pytest.fixture): Fixture providing a temporary directory path
    for testing.

Tests:
    - `test_student_data_insertion`: Verifies correct insertion of student
       data intonthe database.
    - `test_insert_and_retrieve_complete_data`: Tests full retrieval of a
       student'sdata using the StudentList class.
    - `test_invalid_student_id`: Tests handling of non-existent student IDs.
    - `test_insert_invalid_data_types`: Ensures graceful handling of incorrect
       data types.
    - `test_update_student_record`: Tests updating a student's record.
    - `test_delete_student_record`: Tests deleting a student's record.
    - `test_invalid_update_student_record`: Tests updating a non-existent
       student's record.
    - `test_invalid_delete_student_record`: Tests deleting a non-existent
       student's record.
    - `test_export_data`: Tests exporting student data to a TSV file.
    - `test_max_score_calculation`: Tests the maximum score for a subject.
    - `test_min_score_calculation`: Tests the minimum score for a subject.
    - `test_avg_score_calculation`: Tests the mean score for a subject.

"""

from pathlib import Path
from typing import Generator

import pytest

from student import Grades, StudentList, StudentManager


# For the student_manager fixture
@pytest.fixture(scope="function")
def student_manager(tmp_path: Path) -> Generator[StudentManager, None, None]:
    """Provides instance of StudentManager with fresh database for testing."""
    db_path = tmp_path / "student.db"
    manager = StudentManager(str(db_path))
    manager.create_tables()
    yield manager


# For the load_data fixture
@pytest.fixture(scope="function")
def load_data(student_manager: StudentManager) -> Generator[None, None, None]:
    """Loads test data into the fresh database."""
    # the test data files are located in the tests/data directory
    student_data_file = "tests/fake_student_table.tsv"
    student_manager.parse_data(student_data_file)
    yield


def test_student_data_insertion(
    student_manager: StudentManager, load_data: None
) -> None:
    """Verifies that student data is correctly inserted into the database."""
    conn = student_manager.connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM student WHERE ID = \
                '53821'"
        )
        result = cursor.fetchone()
        assert result == (
            "53821",
            "Walt",
            "Male",
            "9-1-2022",
            "78",
            "93",
            "86",
            "95",
            "88",
        ), "Student data insertion failed or data corrupted"
    finally:
        conn.close()


def test_insert_and_retrieve_complete_data(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests full retrieval of a student's data using the StudentList class."""
    conn = student_manager.connect()
    try:
        student_list = StudentList(connection=conn, students_id="53821")
        assert student_list.student_name == "Walt", "Name retrieval failed"
    finally:
        conn.close()


def test_invalid_student_id(student_manager: StudentManager) -> None:
    """Tests handling of non-existent student ID."""
    conn = student_manager.connect()
    try:
        student_list = StudentList(connection=conn, students_id="99999")
        assert (
            student_list.student_name is None
        ), "Should return None for non-existent student ID"
    finally:
        conn.close()


def test_insert_invalid_data_types(student_manager: StudentManager) -> None:
    """Ensures that the system handles incorrect data types gracefully."""
    # Inserting data with invalid types
    invalid_data = {
        "ID": "9999",
        "Name": "Invalid",
        "Gender": "Male",
        "Enroll_Date": "99-99-9999",
        "English": "InvalidGrade",
        "Math": "95",
        "History": "88",
        "Science": "92",
        "Arts": "90",
    }
    # Test data type validation
    student_manager.insert_student(invalid_data)
    # Check if data is inserted
    conn = student_manager.connect()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM student WHERE ID = '9999'")
        result = cursor.fetchone()
        assert (
            result is not None
        ), "Data should be inserted even with invalid types"
    finally:
        conn.close()


def test_update_student_record(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests updating a student's record."""
    # Update English grade for student ID '53821'
    update_data = {"English": "85"}  # Updated grade
    assert student_manager.update_student(
        "53821", **update_data
    ), "Update failed"

    # Verify the updated data
    conn = student_manager.connect()
    try:
        student_list = StudentList(connection=conn, students_id="53821")
        assert (
            student_list.student_english == "85"
        ), "English grade update failed"
    finally:
        conn.close()


def test_delete_student_record(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests deleting a student's record."""
    # Delete student ID '53821'
    assert student_manager.delete_student("53821"), "Deletion failed"

    # Verify that the student is deleted
    conn = student_manager.connect()
    try:
        student_list = StudentList(connection=conn, students_id="53821")
        assert student_list.student_id is None, "Student should be deleted"
    finally:
        conn.close()


def test_invalid_update_student_record(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests updating a non-existent student's record."""
    # Update English grade for non-existent student ID '99999'
    update_data = {"English": "85"}  # Updated grade
    assert not student_manager.update_student(
        "99999", **update_data
    ), "Update should fail for non-existent student"


def test_invalid_delete_student_record(
    student_manager: StudentManager,
) -> None:
    """Tests deleting a non-existent student's record."""
    # Delete non-existent student ID '99999'
    assert not student_manager.delete_student(
        "99999"
    ), "Deletion should fail for non-existent student"


def test_export_data(student_manager: StudentManager, tmp_path: Path) -> None:
    """Tests exporting student data to a TSV file."""
    # Call the export_data function
    filename = tmp_path / "test_export.tsv"
    student_manager.export_data(str(filename))

    # Check if the file has been created
    assert filename.exists(), "Exported file does not exist"

    # Check if the file is not empty
    assert filename.stat().st_size > 0, "Exported file is empty"


def test_max_score_calculation(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests the calculation of the maximum score for a specific subject."""
    conn = student_manager.connect()
    try:
        max_score = Grades.get_max_score(conn, "Math")
        expected_max_score = 99
        assert (
            int(max_score) == expected_max_score
        ), f"Expected {expected_max_score}, got {max_score}"
    finally:
        conn.close()


def test_min_score_calculation(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests the calculation of the minimum score for a specific subject."""
    conn = student_manager.connect()
    try:
        min_score = Grades.get_min_score(conn, "Math")
        expected_min_score = 77
        assert (
            int(min_score) == expected_min_score
        ), f"Expected {expected_min_score}, got {min_score}"
    finally:
        conn.close()


def test_avg_score_calculation(
    student_manager: StudentManager, load_data: None
) -> None:
    """Tests the calculation of the average score for a specific subject."""
    conn = student_manager.connect()
    try:
        avg_score = Grades.get_avg_score(conn, "Math")
        expected_avg_score = 88.2
        assert (
            float(avg_score) == expected_avg_score
        ), f"Expected {expected_avg_score}, got {avg_score}"
    finally:
        conn.close()
