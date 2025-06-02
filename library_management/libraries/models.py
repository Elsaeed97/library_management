from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Library(models.Model):
    name = models.CharField(_("Library Name"), max_length=200)
    address = models.TextField(_("Address"))
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6)
    phone = models.CharField(_("Phone Number"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Library")
        verbose_name_plural = _("Libraries")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    bio = models.TextField(_("Biography"), blank=True)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField(_("Title"), max_length=300)
    isbn = models.CharField(_("ISBN"), max_length=13, unique=True)
    authors = models.ManyToManyField(
        Author,
        verbose_name=_("Authors"),
        related_name="authored_books",
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_("Category"),
        on_delete=models.CASCADE,
        related_name="category_books",
    )
    library = models.ForeignKey(
        Library,
        verbose_name=_("Library"),
        on_delete=models.CASCADE,
        related_name="library_books",
    )
    publication_year = models.IntegerField(
        _("Publication Year"),
        validators=[MinValueValidator(1000), MaxValueValidator(timezone.now().year)],
    )
    total_copies = models.PositiveIntegerField(_("Total Copies"), default=1)
    available_copies = models.PositiveIntegerField(_("Available Copies"), default=1)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Model validation"""
        if self.available_copies > self.total_copies:
            msg = "Available copies cannot exceed total copies"
            raise ValidationError(msg)
        if self.available_copies < 0:
            msg = "Available copies cannot be negative"
            raise ValidationError(msg)

    @property
    def is_available(self):
        return self.available_copies > 0

    def borrow_copy(self):
        """Decrease available copies when borrowed"""
        if self.available_copies > 0:
            self.available_copies -= 1
            self.save()
            return True
        return False

    def return_copy(self):
        """Increase available copies when returned.
        Also notify if book was previously unavailable.
        """
        if self.available_copies < self.total_copies:
            was_unavailable = self.available_copies == 0
            self.available_copies += 1
            self.save()

            if was_unavailable:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "book_availability",
                    {
                        "type": "book_available",
                        "message": f"'{self.title}' is now available!",
                    },
                )
            return True
        return False


class BorrowingTransaction(models.Model):
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("returned", _("Returned")),
        ("overdue", _("Overdue")),
    ]

    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="borrowing_transactions_user",
    )
    books = models.ManyToManyField(
        Book,
        verbose_name=_("Books"),
        related_name="borrowing_transactions_books",
    )
    borrow_date = models.DateTimeField(_("Borrow Date"), auto_now_add=True)
    expected_return_date = models.DateField(_("Expected Return Date"))
    actual_return_date = models.DateTimeField(
        _("Actual Return Date"),
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
    )
    penalty_amount = models.DecimalField(
        _("Penalty Amount"),
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )

    MAX_BORROW_LIMIT = 3

    class Meta:
        verbose_name = _("Borrowing Transaction")
        verbose_name_plural = _("Borrowing Transactions")

    def __str__(self):
        return f"{self.user.email} - {self.borrow_date.date()}"

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop("skip_validation", False)
        if not skip_validation:
            self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Model validation"""
        if self.expected_return_date:
            max_return_date = timezone.now().date() + timedelta(days=30)
            if self.expected_return_date > max_return_date:
                msg = "Return date cannot exceed 30 days from today"
                raise ValidationError(msg)

            if self.expected_return_date <= timezone.now().date():
                msg = "Return date must be in the future"
                raise ValidationError(msg)

    @property
    def is_overdue(self):
        if self.status == "returned":
            return False
        return timezone.now().date() > self.expected_return_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.expected_return_date).days

    @property
    def book_count(self):
        return self.books.count()

    def calculate_penalty(self, daily_penalty=1.00):
        """Calculate penalty amount (doesn't save)"""
        if self.is_overdue:
            return self.days_overdue * daily_penalty
        return 0.00

    @classmethod
    def validate_user_borrowing_limit(cls, user, new_books_count=0):
        """Check if user can borrow more books"""
        active_transactions = cls.objects.filter(
            user=user,
            status__in=["active", "overdue"],
        )
        total_active_books = sum(t.books.count() for t in active_transactions)

        if total_active_books + new_books_count > cls.MAX_BORROW_LIMIT:
            error_message = (
                f"Cannot borrow {new_books_count} book(s). "
                f"You currently have {total_active_books} active books. "
                f"Maximum allowed is {cls.MAX_BORROW_LIMIT} books."
            )
            raise ValidationError(error_message)
        return True

    @classmethod
    def can_user_borrow(cls, user, books_to_borrow):
        """Check if user can borrow specific books"""
        cls.validate_user_borrowing_limit(user, len(books_to_borrow))
        for book in books_to_borrow:
            if not book.is_available:
                msg = f"Book '{book.title}' is not available"
                raise ValidationError(msg)
        return True

    @classmethod
    def get_user_active_book_count(cls, user):
        """Get current number of active borrowed books for a user"""
        active_transactions = cls.objects.filter(
            user=user,
            status__in=["active", "overdue"],
        )
        return sum(t.books.count() for t in active_transactions)
