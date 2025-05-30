# serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import Category
from library_management.libraries.models import Library

User = get_user_model()


class LibrarySerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(read_only=True)
    distance = serializers.FloatField(read_only=True)

    class Meta:
        model = Library
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "phone",
            "email",
            "created_at",
            "book_count",
            "distance",
        ]
        read_only_fields = ["created_at"]


class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Author
        fields = [
            "id",
            "first_name",
            "last_name",
            "bio",
            "birth_date",
            "book_count",
        ]


class AuthorNameSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ["id", "full_name"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CategoryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class LibraryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ["id", "name"]


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorNameSerializer(many=True, read_only=True)
    category = CategoryNameSerializer(read_only=True)
    library = LibraryNameSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "isbn",
            "authors",
            "category",
            "library",
            "publication_year",
            "available_copies",
            "total_copies",
            "is_available",
        ]

    read_only_fields = ["available_copies", "total_copies"]


class BookNestedSerializer(serializers.ModelSerializer):
    category = CategoryNameSerializer(read_only=True)
    library = LibraryNameSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "isbn",
            "library",
            "publication_year",
            "available_copies",
            "total_copies",
            "is_available",
            "category",
        ]


class LoadedAuthorSerializer(serializers.ModelSerializer):
    books = BookNestedSerializer(source="authored_books", many=True, read_only=True)

    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name", "bio", "birth_date", "books"]
