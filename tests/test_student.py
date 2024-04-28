import datetime
import sqlite3
from typing import Generator
from pathlib import Path
import pytest
from src.student import StudentManager, StudentList


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
    try:
        student_manager.insert_student(invalid_data)
    except ValueError as e:
        assert (
            str(e) == "IntegrityError: UNIQUE constraint failed: student.ID"
        ), "Unexpected error message"
    except sqlite3.IntegrityError:
        # ID already exists, which violates the uniqueness constraint
        pass
    else:
        pytest.fail("Expected IntegrityError but no exception was raised")


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
