from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from library_management.libraries.models import BorrowingTransaction


@shared_task
def send_borrow_confirmation_email(user_email, book_titles, expected_return_date):
    subject = "Borrowing Confirmation"
    context = {
        "books": book_titles,
        "expected_return_date": expected_return_date,
    }

    message = render_to_string("emails/borrow_confirmation.txt", context)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )


@shared_task
def send_due_soon_reminders():
    today = timezone.now().date()
    due_soon_range = [today + timedelta(days=i) for i in range(1, 4)]

    transactions = (
        BorrowingTransaction.objects.filter(
            status="active",
            expected_return_date__in=due_soon_range,
        )
        .select_related("user")
        .prefetch_related("books")
    )

    for tx in transactions:
        user = tx.user
        books = tx.books.all()
        context = {
            "books": [b.title for b in books],
            "expected_return_date": tx.expected_return_date,
        }

        message = render_to_string("emails/borrow_reminder.txt", context)

        send_mail(
            subject="Return Reminder",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
