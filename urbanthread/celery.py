import os
from celery import Celery
from celery.schedules import crontab

# ── Tell Celery which Django settings to use ──────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "urbanthread.settings")

app = Celery("urbanthread")

# ── Pull all CELERY_* keys from Django settings ───────────────────────────────
app.config_from_object("django.conf:settings", namespace="CELERY")

# ── Auto-discover tasks.py in every INSTALLED_APP ─────────────────────────────
app.autodiscover_tasks()


# ── Periodic tasks (Celery Beat) ──────────────────────────────────────────────
app.conf.beat_schedule = {

    # ── Coupons ───────────────────────────────────────────────────────────────
    # Deactivate coupons whose expiration_date has passed — runs every midnight
    "deactivate-expired-coupons": {
        "task": "coupons.tasks.deactivate_expired_coupons",
        "schedule": crontab(hour=0, minute=0),      # 00:00 asia/dhaka daily
    },

    # ── Orders ────────────────────────────────────────────────────────────────
    # Send a daily summary email to admins (orders placed yesterday)
    "daily-order-summary": {
        "task": "orders.tasks.send_daily_order_summary",
        "schedule": crontab(hour=8, minute=0),       # 08:00 asia/dhaka daily
    },

    # Auto-cancel orders that are still 'pending' after 24 hours
    # (e.g. customer never completed payment)
    "auto-cancel-stale-orders": {
        "task": "orders.tasks.auto_cancel_stale_orders",
        "schedule": crontab(hour="*/6", minute=0),   # every 6 hours
    },

    # ── Inventory ─────────────────────────────────────────────────────────────
    # Alert admins about low-stock variants — runs every morning
    "low-stock-alert": {
        "task": "orders.tasks.send_low_stock_alert",
        "schedule": crontab(hour=7, minute=0),       # 07:00 asia/dhaka daily
    },

    # ── Cart ──────────────────────────────────────────────────────────────────
    # Remind users who left items in cart > 24 h without ordering
    "abandoned-cart-reminder": {
        "task": "orders.tasks.send_abandoned_cart_reminders",
        "schedule": crontab(hour=10, minute=0),      # 10:00 asia/dhaka daily
    },
}

app.conf.timezone = "Asia/Dhaka"
