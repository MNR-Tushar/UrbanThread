"""Shared cache-backed limits for OTP and outbound email sending."""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


class EmailRateLimitExceeded(RuntimeError):
    """Raised when an email send is blocked by an application quota."""


def _increment_with_expiry(key, timeout, amount=1):
    """Atomically increment a cache counter, initializing it when absent."""
    try:
        if cache.add(key, amount, timeout=timeout):
            return amount
        try:
            return cache.incr(key, delta=amount)
        except ValueError:
            # The key expired between add() and incr().
            return amount if cache.add(key, amount, timeout=timeout) else None
    except Exception:
        # Fail closed: a cache outage must not disable email-abuse protection.
        return None


def _email_fingerprint(email):
    normalized = (email or '').strip().casefold().encode('utf-8')
    return hashlib.sha256(normalized).hexdigest()


def reserve_otp_email_slot(email):
    """Allow at most one OTP email per minute and three in any hour per address."""
    fingerprint = _email_fingerprint(email)
    cooldown_key = f'email-otp-cooldown:{fingerprint}'
    cooldown_seconds = getattr(settings, 'EMAIL_OTP_COOLDOWN_SECONDS', 60)
    try:
        if not cache.add(cooldown_key, 1, timeout=cooldown_seconds):
            return False
    except Exception:
        return False

    hour_key = f'email-otp-hour:{fingerprint}'
    count = _increment_with_expiry(hour_key, 3600)
    per_hour_limit = getattr(settings, 'EMAIL_OTP_PER_ADDRESS_PER_HOUR', 3)
    return count is not None and count <= per_hour_limit


def reserve_daily_email_slot(amount=1):
    """Cap application email sends below the Brevo free-plan daily allowance."""
    limit = getattr(settings, 'EMAIL_DAILY_SEND_CAP', 250)
    day = timezone.localdate().isoformat()
    key = f'outbound-email-count:{day}'
    count = _increment_with_expiry(
        key,
        int(timedelta(days=2).total_seconds()),
        amount=max(int(amount), 1),
    )
    if count is None or count > limit:
        raise EmailRateLimitExceeded(
            'The application daily email sending limit has been reached.'
        )
