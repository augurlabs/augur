import pytest
from augur.tasks.git.util.facade_worker.facade_worker.analyzecommit import check_swapped_emails

def test_correct_input_unchanged():
    name, email = check_swapped_emails("John Smith", "john@gmail.com")
    assert name == "John Smith"
    assert email == "john@gmail.com"

def test_swapped_input_is_corrected():
    name, email = check_swapped_emails("john@gmail.com", "John Smith")
    assert name == "John Smith"
    assert email == "john@gmail.com"

def test_name_field_contains_mixed_name_and_email():
    # name field has both a name and email mixed together
    name, email = check_swapped_emails("John Smith john@gmail.com", "")
    assert name == "John Smith john@gmail.com"
    assert email == ""

def test_email_field_contains_mixed_name_and_email():
    # email field has both a name and email mixed together
    name, email = check_swapped_emails("John Smith", "John Smith john@gmail.com")
    assert name == "John Smith"
    assert email == "John Smith john@gmail.com"

def test_both_fields_contain_mixed_name_and_email():
    name, email = check_swapped_emails("John Smith john@gmail.com", "Jane Doe jane@gmail.com")
    assert name == "John Smith john@gmail.com"
    assert email == "Jane Doe jane@gmail.com"

def test_when_both_empty_strings():
    name, email = check_swapped_emails("", "")
    assert name == ""
    assert email == ""

def test_email_with_multiple_at_signs():
    name, email = check_swapped_emails("John Smith", "john@@gmail.com")
    assert name == "John Smith"
    assert email == "john@@gmail.com"