from celery import shared_task
from django.core.mail import send_mail

from .models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


@shared_task
def send_password_reset_email(subject, message, from_email, recipient_list):
    send_mail(subject, message, from_email, recipient_list)
