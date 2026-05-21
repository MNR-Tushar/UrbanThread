import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


# ─── Welcome Email ────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,          # retry after 60 s on transient failure
    name="accounts.tasks.send_welcome_email",
)
def send_welcome_email(self, user_id: int) -> str:
    """
    Send a welcome email to a newly registered user.

    Called from accounts/views.py → UserRegisterationAPIView.post()
    immediately after the user record is created (non-blocking).

    Args:
        user_id: Primary key of the new CustomUser.

    Returns:
        A short status string logged by Flower / the result backend.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        # User was deleted before the task ran — nothing to do.
        logger.warning("send_welcome_email: user %s not found, skipping.", user_id)
        return f"skipped: user {user_id} not found"

    subject = "Welcome to Urban Thread! 🎉"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    # ── Plain-text body ───────────────────────────────────────────────────────
    text_body = f"""
Hi {user.first_name or user.username},

Welcome to Urban Thread — your destination for premium urban fashion.

Your account is ready. Start exploring our latest collections:
{settings.FRONTEND_URL}/products

Need help? Reply to this email and we'll get back to you within 24 hours.

— The Urban Thread Team
""".strip()

    # ── HTML body ─────────────────────────────────────────────────────────────
    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
  <h2 style="color:#1a1a1a;">Welcome to Urban Thread! 🎉</h2>
  <p>Hi <strong>{user.first_name or user.username}</strong>,</p>
  <p>Your account has been created successfully. We're excited to have you!</p>
  <a href="{settings.FRONTEND_URL}/products"
     style="display:inline-block;padding:12px 24px;background:#1a1a1a;
            color:#fff;text-decoration:none;border-radius:4px;margin:16px 0;">
    Shop Now
  </a>
  <p style="color:#666;font-size:13px;">
    If you didn't create this account, please ignore this email.
  </p>
  <hr style="border:none;border-top:1px solid #eee;">
  <p style="color:#999;font-size:12px;">© Urban Thread. All rights reserved.</p>
</body>
</html>
""".strip()

    try:
        msg = EmailMultiAlternatives(subject, text_body, from_email, to)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("send_welcome_email: sent to %s", user.email)
        return f"sent to {user.email}"

    except Exception as exc:
        logger.error(
            "send_welcome_email: failed for user %s — %s. Retrying…",
            user_id, exc
        )
        raise self.retry(exc=exc)


# ─── Password Reset Email ─────────────────────────────────────────────────────

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="accounts.tasks.send_password_reset_email",
)
def send_password_reset_email(self, user_id: int, reset_url: str) -> str:
    """
    Send a password-reset link email.

    Args:
        user_id:   PK of the user requesting a reset.
        reset_url: Full frontend URL containing the reset token.

    Returns:
        Status string.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return f"skipped: user {user_id} not found"

    subject = "Reset your Urban Thread password"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    text_body = f"""
Hi {user.first_name or user.username},

We received a request to reset your password.
Click the link below (valid for 1 hour):

{reset_url}

If you didn't request this, you can safely ignore this email.

— The Urban Thread Team
""".strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
  <h2 style="color:#1a1a1a;">Password Reset Request</h2>
  <p>Hi <strong>{user.first_name or user.username}</strong>,</p>
  <p>Click the button below to reset your password. This link expires in <strong>1 hour</strong>.</p>
  <a href="{reset_url}"
     style="display:inline-block;padding:12px 24px;background:#e63946;
            color:#fff;text-decoration:none;border-radius:4px;margin:16px 0;">
    Reset Password
  </a>
  <p style="color:#666;font-size:13px;">
    If you didn't request this, please ignore this email — your password won't change.
  </p>
</body>
</html>
""".strip()

    try:
        msg = EmailMultiAlternatives(subject, text_body, from_email, to)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("send_password_reset_email: sent to %s", user.email)
        return f"sent to {user.email}"
    except Exception as exc:
        raise self.retry(exc=exc)