# admin.py
from django.contrib import admin

from .models import Author
from .models import Book
from .models import BorrowingTransaction
from .models import Category
from .models import Library


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ["name", "address", "phone", "email"]
    search_fields = ["name", "address"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "birth_date"]
    search_fields = ["first_name", "last_name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "isbn",
        "category",
        "library",
        "available_copies",
        "total_copies",
    ]
    list_filter = ["category", "library"]
    search_fields = ["title", "isbn"]
    filter_horizontal = ["authors"]


@admin.register(BorrowingTransaction)
class BorrowingTransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "borrow_date", "expected_return_date", "status"]
    list_filter = ["status", "borrow_date"]
    filter_horizontal = ["books"]
