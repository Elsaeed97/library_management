import django_filters

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import Library


class LibraryFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="library_books__category__name",
        lookup_expr="iexact",
    )
    author = django_filters.CharFilter(
        field_name="library_books__authors__last_name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Library
        fields = ["category", "author"]


class AuthorFilter(django_filters.FilterSet):
    library = django_filters.CharFilter(
        field_name="authored_books__library__name",
        lookup_expr="iexact",
    )
    category = django_filters.CharFilter(
        field_name="authored_books__category__name",
        lookup_expr="iexact",
    )

    class Meta:
        model = Author
        fields = ["library", "category"]


class BookFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__name",
        lookup_expr="iexact",
    )
    library = django_filters.CharFilter(
        field_name="library__name",
        lookup_expr="iexact",
    )
    author = django_filters.CharFilter(
        field_name="authors__last_name",
        lookup_expr="iexact",
    )

    class Meta:
        model = Book
        fields = ["category", "library", "author"]


class LoadedAuthorFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="authored_books__category__name",
        lookup_expr="iexact",
    )
    library = django_filters.CharFilter(
        field_name="authored_books__library__name",
        lookup_expr="iexact",
    )

    class Meta:
        model = Author
        fields = ["category", "library"]
