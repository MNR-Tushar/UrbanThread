from celery import shared_task
from django.utils import timezone

from coupons.models import Coupon


@shared_task(name="coupons.tasks.deactivate_expired_coupons")
def deactivate_expired_coupons() -> str:
    today = timezone.localdate()
    updated = Coupon.objects.filter(is_active=True, expiration_date__lt=today).update(is_active=False)
    return f"deactivated:{updated}"


@shared_task(name="coupons.tasks.activate_scheduled_campaigns")
def activate_scheduled_campaigns() -> str:
    today = timezone.localdate()
    updated = Coupon.objects.filter(
        is_active=False,
        start_date__isnull=False,
        start_date__lte=today,
        expiration_date__gte=today,
    ).update(is_active=True)
    return f"activated:{updated}"
