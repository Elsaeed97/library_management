import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.status import HTTP_200_OK
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import Category
from library_management.libraries.models import Library

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user(db):
    return User.objects.create_user(
        email="member@test.com", password="testpassword", role="member",  # noqa: S106
    )


@pytest.fixture
def auth_client(api_client, member_user):
    api_client.force_authenticate(user=member_user)
    return api_client


@pytest.fixture
def sample_data(member_user):
    library = Library.objects.create(
        name="Main Branch", address="123 St", latitude=30.0, longitude=31.0,
    )
    category = Category.objects.create(name="Sci-Fi")
    author = Author.objects.create(first_name="Isaac", last_name="Asimov")
    book = Book.objects.create(
        title="Foundation",
        isbn="1234567890123",
        category=category,
        library=library,
        total_copies=5,
        available_copies=5,
        publication_year=1951,
    )
    book.authors.add(author)
    return {
        "library": library,
        "category": category,
        "author": author,
        "book": book,
        "user": member_user,
    }


# LIBRARY TEST
def test_library_list(api_client, sample_data):
    res = api_client.get("/api/libraries/")
    assert res.status_code == HTTP_200_OK
    assert len(res.data["results"]) >= 1


def test_library_distance_filter(api_client, sample_data):
    res = api_client.get("/api/libraries/?latitude=30.01&longitude=31.01")
    assert res.status_code == HTTP_200_OK
    assert "distance" in res.data["results"][0]


# AUTHOR TEST
def test_author_filter_by_category(api_client, sample_data):
    res = api_client.get(f"/api/authors/?category={sample_data['category'].name}")
    assert res.status_code == HTTP_200_OK
    assert "book_count" in res.data["results"][0]


# BOOK TEST
def test_book_list(api_client, sample_data):
    res = api_client.get("/api/books/")
    assert res.status_code == HTTP_200_OK
    assert res.data["results"][0]["title"] == "Foundation"


#  LOADED AUTHOR TEST
def test_loaded_authors(api_client, sample_data):
    res = api_client.get("/api/loaded-authors/")
    assert res.status_code == HTTP_200_OK
    assert "books" in res.data["results"][0]


# BORROW/RETURN TEST
def test_borrow_and_return_flow(auth_client, sample_data):
    book = sample_data["book"]
    user = sample_data["user"]  # noqa: F841

    # Borrow
    tomorrow = timezone.now().date() + datetime.timedelta(days=1)
    borrow_payload = {
        "books": [book.id],
        "expected_return_date": tomorrow,
    }

    borrow_res = auth_client.post("/api/borrow/", borrow_payload, format="json")
    assert borrow_res.status_code == HTTP_201_CREATED
    tx_id = borrow_res.data["id"]

    # Return
    return_res = auth_client.post(f"/api/borrow/{tx_id}/return/")
    assert return_res.status_code == HTTP_200_OK
    assert return_res.data["status"] == "returned"
