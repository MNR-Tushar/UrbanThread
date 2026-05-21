import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.db.models import Count, Sum
from django.utils import timezone

from orders.models import Order

logger = logging.getLogger(__name__)


@shared_task(name="orders.tasks.send_order_invoice_email", max_retries=3, default_retry_delay=60)
def send_order_invoice_email(order_id: int) -> str:
    try:
        order = Order.objects.select_related("user").prefetch_related("items__product").get(pk=order_id)
    except Order.DoesNotExist:
        return f"skipped: order {order_id} not found"

    customer_name = order.user.first_name or order.user.username or "Customer"
    item_lines = [
        f"- {item.product.product_name} x{item.quantity} @ {item.price}"
        for item in order.items.all()
    ]
    body = (
        f"Hi {customer_name},\n\n"
        f"Thanks for your order {order.order_number}.\n"
        f"Payment status: {order.payment_status}\n"
        f"Order status: {order.order_status}\n"
        f"Total: {order.total_amount} BDT\n\n"
        "Items:\n"
        f"{chr(10).join(item_lines)}\n\n"
        "Urban Thread"
    )

    msg = EmailMultiAlternatives(
        subject=f"Invoice - {order.order_number}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )
    msg.send(fail_silently=False)
    return f"invoice_sent:{order.order_number}"


@shared_task(name="orders.tasks.sync_order_stock", max_retries=2, default_retry_delay=30)
def sync_order_stock(order_id: int) -> str:
    from inventory.models import Inventory

    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        return f"skipped: order {order_id} not found"

    mismatches = []
    for item in order.items.all():
        inv = Inventory.objects.filter(
            product=item.product, color=item.color, size=item.size
        ).first()
        if not inv:
            mismatches.append(f"missing_inventory:{item.id}")
        elif inv.quantity < 0:
            mismatches.append(f"negative_stock:{inv.id}")

    if mismatches:
        logger.warning("stock sync issues for order %s: %s", order.order_number, mismatches)
        return f"issues:{','.join(mismatches)}"
    return f"ok:{order.order_number}"


@shared_task(name="orders.tasks.push_order_analytics_event")
def push_order_analytics_event(order_id: int, event_name: str = "order_placed") -> str:
    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        return f"skipped: order {order_id} not found"

    payload = {
        "event": event_name,
        "order_id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "total_amount": str(order.total_amount),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "item_count": order.items.count(),
        "created_at": order.created_at.isoformat(),
    }
    logger.info("analytics_event=%s", json.dumps(payload))
    return f"analytics_logged:{order.order_number}"


@shared_task(name="orders.tasks.send_daily_order_summary")
def send_daily_order_summary() -> str:
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today - timedelta(days=1), datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    qs = Order.objects.filter(created_at__gte=start, created_at__lt=end)
    total_orders = qs.count()
    total_revenue = qs.aggregate(total=Sum("total_amount"))["total"] or 0
    status_breakdown = list(qs.values("order_status").annotate(count=Count("id")).order_by("order_status"))

    summary = (
        f"Daily order summary ({today - timedelta(days=1)}):\n"
        f"Total orders: {total_orders}\n"
        f"Total revenue: {total_revenue} BDT\n"
        f"Statuses: {status_breakdown}"
    )
    mail_admins("UrbanThread Daily Order Summary", summary, fail_silently=True)
    return f"summary_sent:{total_orders}_orders"


@shared_task(name="orders.tasks.auto_cancel_stale_orders")
def auto_cancel_stale_orders() -> str:
    threshold = timezone.now() - timedelta(hours=24)
    stale_orders = Order.objects.filter(order_status="pending", created_at__lt=threshold)
    updated = stale_orders.update(order_status="cancelled")
    return f"auto_cancelled:{updated}"


@shared_task(name="orders.tasks.generate_sales_report")
def generate_sales_report(start_date: str = "", end_date: str = "", fmt: str = "csv") -> str:
    report_dir = Path(settings.BASE_DIR) / "media" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    today = timezone.localdate()
    if not end_date:
        end_date = str(today)
    if not start_date:
        start_date = str(today - timedelta(days=30))

    orders = (
        Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        .select_related("user")
        .order_by("-created_at")
    )
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    report_base = f"sales_report_{start_date}_to_{end_date}_{ts}"

    if fmt.lower() == "pdf":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            file_path = report_dir / f"{report_base}.pdf"
            pdf = canvas.Canvas(str(file_path), pagesize=A4)
            y = 800
            pdf.drawString(40, y, f"Sales Report: {start_date} to {end_date}")
            y -= 30
            for order in orders[:300]:
                line = f"{order.order_number} | {order.user.email} | {order.total_amount} | {order.order_status}"
                pdf.drawString(40, y, line[:110])
                y -= 18
                if y < 60:
                    pdf.showPage()
                    y = 800
            pdf.save()
            return str(file_path)
        except Exception as exc:
            logger.warning("PDF generation failed (%s); falling back to CSV", exc)

    file_path = report_dir / f"{report_base}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["order_number", "customer_email", "total_amount", "payment_status", "order_status", "created_at"])
        for order in orders:
            writer.writerow([
                order.order_number,
                order.user.email,
                str(order.total_amount),
                order.payment_status,
                order.order_status,
                order.created_at.isoformat(),
            ])
    return str(file_path)
