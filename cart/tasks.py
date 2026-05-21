from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from cart.models import Cart


@shared_task(name="cart.tasks.send_abandoned_cart_reminders")
def send_abandoned_cart_reminders(hours: int = 24) -> str:
    threshold = timezone.now() - timedelta(hours=hours)
    carts = (
        Cart.objects.select_related("user")
        .prefetch_related("items__product")
        .filter(updated_at__lt=threshold)
    )
    sent = 0

    for cart in carts:
        items = list(cart.items.all())
        if not items or not cart.user.email:
            continue

        lines = [f"- {x.product.product_name} x{x.quantity}" for x in items[:20]]
        body = (
            f"Hi {cart.user.first_name or cart.user.username},\n\n"
            "You left items in your cart. Complete your order before they go out of stock.\n\n"
            + "\n".join(lines)
            + f"\n\nShop now: {settings.FRONTEND_URL}/cart\n\nUrban Thread"
        )

        msg = EmailMultiAlternatives(
            subject="You still have items in your Urban Thread cart",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cart.user.email],
        )
        msg.send(fail_silently=True)
        sent += 1

    return f"reminders_sent:{sent}"
