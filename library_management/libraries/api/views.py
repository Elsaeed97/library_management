from django.db.models import Count
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Func
from django.db.models import Prefetch
from django.db.models import Q
from django.db.models import Value
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from library_management.libraries.models import Author
from library_management.libraries.models import Book
from library_management.libraries.models import BorrowingTransaction
from library_management.libraries.models import Library

from .filters import AuthorFilter
from .filters import BookFilter
from .filters import LibraryFilter
from .filters import LoadedAuthorFilter
from .serializers import AuthorSerializer
from .serializers import BookSerializer
from .serializers import BorrowingTransactionCreateSerializer
from .serializers import BorrowingTransactionReturnSerializer
from .serializers import LibrarySerializer
from .serializers import LoadedAuthorSerializer


class Radians(Func):
    function = "RADIANS"
    arity = 1


class Cos(Func):
    function = "COS"
    arity = 1


class Sin(Func):
    function = "SIN"
    arity = 1


class ACos(Func):
    function = "ACOS"
    arity = 1


class LibraryViewSet(viewsets.ModelViewSet):
    serializer_class = LibrarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LibraryFilter
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Library.objects.annotate(book_count=Count("library_books"))

        lat = self.request.query_params.get("latitude")
        lon = self.request.query_params.get("longitude")

        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)

                queryset = queryset.annotate(
                    distance=ExpressionWrapper(
                        6371
                        * ACos(
                            Cos(Radians(Value(lat)))
                            * Cos(Radians(F("latitude")))
                            * Cos(Radians(F("longitude") - Value(lon)))
                            + Sin(Radians(Value(lat))) * Sin(Radians(F("latitude"))),
                        ),
                        output_field=FloatField(),
                    ),
                ).order_by("distance")
            except ValueError:
                pass

        return queryset


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuthorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AuthorFilter
    http_method_names = ["get"]

    def get_queryset(self):
        library = self.request.query_params.get("library")
        category = self.request.query_params.get("category")

        book_filter = Q()
        if library:
            book_filter &= Q(authored_books__library__name__iexact=library)
        if category:
            book_filter &= Q(authored_books__category__name__iexact=category)

        return Author.objects.annotate(
            book_count=Count("authored_books", filter=book_filter),
        )


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookFilter
    http_method_names = ["get"]

    def get_queryset(self):
        return (
            Book.objects.select_related("category", "library")
            .prefetch_related("authors")
            .all()
        )


class LoadedAuthorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoadedAuthorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoadedAuthorFilter
    http_method_names = ["get"]

    def get_queryset(self):
        return Author.objects.prefetch_related(
            Prefetch(
                "authored_books",
                queryset=Book.objects.select_related("category"),
            ),
        )


class BorrowingTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BorrowingTransaction.objects.all()
    serializer_class = BorrowingTransactionCreateSerializer

    def get_queryset(self):
        return BorrowingTransaction.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="return")
    def return_books(self, request, pk=None):
        transaction = self.get_object()

        serializer = BorrowingTransactionReturnSerializer(
            transaction,
            data={},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
