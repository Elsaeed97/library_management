from rest_framework.routers import DefaultRouter

from library_management.libraries.api.views import AuthorViewSet
from library_management.libraries.api.views import BookViewSet
from library_management.libraries.api.views import BorrowingTransactionViewSet
from library_management.libraries.api.views import LibraryViewSet
from library_management.libraries.api.views import LoadedAuthorViewSet

app_name = "libraries"

router = DefaultRouter()
router.register(r"libraries", LibraryViewSet, basename="library")
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"books", BookViewSet, basename="book")
router.register("loaded-authors", LoadedAuthorViewSet, basename="loaded-author")
router.register("borrow", BorrowingTransactionViewSet, basename="borrow")
urlpatterns = router.urls
