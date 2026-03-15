"""Input validation utilities."""
import re


def validate_name(name: str) -> tuple[bool, str]:
    """Validate identity name."""
    if not name or not name.strip():
        return False, "Name cannot be empty"
    if len(name) > 64:
        return False, "Name too long (max 64 characters)"
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
        return False, "Name contains invalid characters"
    return True, ""


def validate_person_id(person_id: str) -> tuple[bool, str]:
    """Validate person ID format."""
    if not person_id:
        return True, ""  # Optional field
    if len(person_id) > 16:
        return False, "ID too long (max 16 characters)"
    if not re.match(r"^[A-Z0-9]+$", person_id):
        return False, "ID must be uppercase alphanumeric"
    return True, ""
