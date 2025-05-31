# serializers.py
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import BorrowingTransaction
from library_management.libraries.models import Category
from library_management.libraries.models import Library
from library_management.libraries.tasks import send_borrow_confirmation_email

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


class BorrowingTransactionCreateSerializer(serializers.ModelSerializer):
    books = serializers.PrimaryKeyRelatedField(many=True, queryset=Book.objects.all())
    expected_return_date = serializers.DateField()

    class Meta:
        model = BorrowingTransaction
        fields = ["id", "books", "expected_return_date"]

    def validate_expected_return_date(self, value):
        today = timezone.now().date()
        max_return_date = today + timedelta(days=30)

        if value <= today:
            msg = "Return date must be in the future."
            raise serializers.ValidationError(msg)
        if value > max_return_date:
            msg = "Return date cannot exceed 30 days from today."
            raise serializers.ValidationError(msg)
        return value

    def validate(self, data):
        user = self.context["request"].user
        books = data.get("books", [])

        BorrowingTransaction.can_user_borrow(user, books)

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        books = validated_data.pop("books")

        with transaction.atomic():
            locked_books = Book.objects.select_for_update().filter(
                id__in=[book.id for book in books],
            )
            unavailable = [book for book in locked_books if not book.is_available]
            if unavailable:
                titles = ", ".join(b.title for b in unavailable)
                msg = f"The following books are not available: {titles}"
                raise serializers.ValidationError(msg)
            BorrowingTransaction.validate_user_borrowing_limit(user, len(books))

            transaction_instance = BorrowingTransaction.objects.create(
                user=user,
                expected_return_date=validated_data["expected_return_date"],
            )
            transaction_instance.books.set(locked_books)
            send_borrow_confirmation_email.delay(
                user.email,
                [book.title for book in locked_books],
                str(transaction_instance.expected_return_date),
            )
            return transaction_instance


class BorrowingTransactionReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowingTransaction
        fields = ["id", "actual_return_date", "status", "penalty_amount"]
        read_only_fields = ["id", "actual_return_date", "penalty_amount"]

    def validate(self, data):
        transaction = self.instance

        if transaction.status == "returned":
            msg = "This transaction is already returned."
            raise serializers.ValidationError(msg)
        return data

    def update(self, instance, validated_data):
        instance.status = "returned"
        instance.save()
        return instance
