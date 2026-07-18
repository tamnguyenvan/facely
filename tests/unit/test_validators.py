"""Unit tests for validators."""
import pytest
from app.utils.validators import validate_name, validate_person_id


def test_validate_name_valid():
    """Test valid name validation."""
    valid, msg = validate_name("John Doe")
    assert valid is True
    assert msg == ""


def test_validate_name_empty():
    """Test empty name validation."""
    valid, msg = validate_name("")
    assert valid is False
    assert "empty" in msg.lower()


def test_validate_name_too_long():
    """Test name too long validation."""
    valid, msg = validate_name("a" * 65)
    assert valid is False
    assert "long" in msg.lower()


def test_validate_name_invalid_chars():
    """Test invalid characters in name."""
    valid, msg = validate_name("John@Doe")
    assert valid is False
    assert "invalid" in msg.lower()


def test_validate_person_id_valid():
    """Test valid person ID."""
    valid, msg = validate_person_id("ABC123")
    assert valid is True
    assert msg == ""


def test_validate_person_id_empty():
    """Test empty person ID (should be valid as optional)."""
    valid, msg = validate_person_id("")
    assert valid is True


def test_validate_person_id_lowercase():
    """Test lowercase person ID (should be invalid)."""
    valid, msg = validate_person_id("abc123")
    assert valid is False
    assert "uppercase" in msg.lower()


def test_validate_person_id_too_long():
    """Test person ID too long."""
    valid, msg = validate_person_id("A" * 17)
    assert valid is False
    assert "long" in msg.lower()
