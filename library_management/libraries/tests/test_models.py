import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import BorrowingTransaction
from library_management.libraries.models import Category
from library_management.libraries.models import Library

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="testpass123")  # noqa: S106


@pytest.fixture
def library(db):
    return Library.objects.create(
        name="ALexandria Library",
        address="ALex, Egypt",
        latitude=30.000,
        longitude=31.000,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Programming")


@pytest.fixture
def author(db):
    return Author.objects.create(first_name="Elsaeed", last_name="Ahmed")


@pytest.fixture
def book(library, category, author):
    book = Book.objects.create(
        title="Introduction to Algorithms",
        isbn="1234567890123",
        category=category,
        library=library,
        publication_year=2000,
        total_copies=2,
        available_copies=2,
    )
    book.authors.add(author)
    return book


def test_book_str_and_availability(book):
    assert str(book) == "Introduction to Algorithms"
    assert book.is_available is True


def test_book_borrow_and_return(book):
    assert book.borrow_copy() is True
    book.refresh_from_db()
    assert book.available_copies == 1

    with patch("library_management.libraries.models.async_to_sync") as mock_async:
        book.available_copies = 0
        book.save()
        book.return_copy()
        book.refresh_from_db()
        assert book.available_copies == 1
        mock_async.assert_called()


def test_book_invalid_available_copies(book):
    book.available_copies = 5
    with pytest.raises(ValidationError):
        book.full_clean()

    book.available_copies = -1
    with pytest.raises(ValidationError):
        book.full_clean()


def test_author_full_name(author):
    assert author.full_name == "Elsaeed Ahmed"


def test_borrowing_transaction_str_and_penalty(user, book):
    tomorrow = timezone.now().date() + datetime.timedelta(days=1)
    tx = BorrowingTransaction.objects.create(
        user=user,
        expected_return_date=tomorrow,
    )
    tx.books.add(book)

    assert str(tx) == f"{user.email} - {tx.borrow_date.date()}"
    assert tx.is_overdue is False
    assert tx.days_overdue == 0
    assert tx.calculate_penalty() == Decimal("0.00")


def test_borrowing_transaction_overdue(user, book):
    overdue_date = timezone.now().date() - datetime.timedelta(days=3)
    tx = BorrowingTransaction(
        user=user,
        expected_return_date=overdue_date,
    )
    tx.save(skip_validation=True)

    tx.books.add(book)

    overdue_days = 3
    assert tx.is_overdue is True
    assert tx.days_overdue == overdue_days
    assert tx.calculate_penalty() == Decimal("3.00")


def test_borrowing_limit_exceeded(user, book):
    for _ in range(3):
        tx = BorrowingTransaction.objects.create(
            user=user,
            expected_return_date=timezone.now().date() + datetime.timedelta(days=7),
        )
        tx.books.add(book)

    with pytest.raises(ValidationError):
        BorrowingTransaction.validate_user_borrowing_limit(user, 1)


def test_expected_return_date_too_far(user):
    invalid_date = timezone.now().date() + datetime.timedelta(days=40)
    tx = BorrowingTransaction(
        user=user,
        expected_return_date=invalid_date,
    )
    with pytest.raises(ValidationError):
        tx.full_clean()
