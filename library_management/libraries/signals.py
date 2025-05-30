# signals.py
from django.db.models.signals import m2m_changed
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import BorrowingTransaction


@receiver(pre_save, sender=BorrowingTransaction)
def update_overdue_status_and_penalty(sender, instance, **kwargs):
    """Update transaction status and penalty if overdue"""
    if getattr(instance, "_skip_signals", False):
        return

    if instance.is_overdue and instance.status == "active":
        instance.status = "overdue"
        instance.penalty_amount = instance.calculate_penalty()


@receiver(m2m_changed, sender=BorrowingTransaction.books.through)
def handle_book_inventory(sender, instance, action, pk_set, **kwargs):
    """Handle book inventory when books are added/removed from transaction"""
    if getattr(instance, "_skip_signals", False):
        return

    if action == "post_add":
        for book_id in pk_set:
            book = instance.books.get(id=book_id)
            book.borrow_copy()

    elif action == "post_remove":
        from .models import Book

        for book_id in pk_set:
            book = Book.objects.get(id=book_id)
            book.return_copy()


@receiver(pre_save, sender=BorrowingTransaction)
def handle_return_process(sender, instance, **kwargs):
    """Handle book returns when status changes to returned"""
    if getattr(instance, "_skip_signals", False):
        return

    if instance.pk:
        try:
            old_instance = BorrowingTransaction.objects.get(pk=instance.pk)
            if old_instance.status != "returned" and instance.status == "returned":
                if not instance.actual_return_date:
                    instance.actual_return_date = timezone.now()
                for book in instance.books.all():
                    book.return_copy()
        except BorrowingTransaction.DoesNotExist:
            pass
