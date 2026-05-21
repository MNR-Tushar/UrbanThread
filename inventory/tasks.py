from celery import shared_task
from django.core.mail import mail_admins

from inventory.models import Inventory


@shared_task(name="inventory.tasks.send_low_stock_alert")
def send_low_stock_alert(threshold: int = 5) -> str:
    low_stock = Inventory.objects.select_related("product", "color", "size").filter(quantity__lte=threshold)
    if not low_stock.exists():
        return "no_low_stock"

    lines = [
        f"{x.product.product_name} / {x.color.color} / {x.size.size_type}: {x.quantity}"
        for x in low_stock[:200]
    ]
    mail_admins(
        subject="UrbanThread Low Stock Alert",
        message="Low stock variants:\n" + "\n".join(lines),
        fail_silently=True,
    )
    return f"alerted:{low_stock.count()}"


@shared_task(name="inventory.tasks.send_restock_notifications")
def send_restock_notifications(restock_threshold: int = 10) -> str:
    restocked = Inventory.objects.select_related("product", "color", "size").filter(quantity__gte=restock_threshold)
    if not restocked.exists():
        return "no_restock"

    # Placeholder for user-specific notifications; currently sends admin digest.
    lines = [
        f"{x.product.product_name} / {x.color.color} / {x.size.size_type}: {x.quantity}"
        for x in restocked[:200]
    ]
    mail_admins(
        subject="UrbanThread Restock Notification",
        message="Recently available variants:\n" + "\n".join(lines),
        fail_silently=True,
    )
    return f"restock_notified:{restocked.count()}"
