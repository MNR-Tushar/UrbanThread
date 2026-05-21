import logging

from celery import shared_task
from django.db import transaction

from payments.models import Payment, PaymentLog
from payments.utils import SSLCommerzPayment

logger = logging.getLogger(__name__)


@shared_task(name="payments.tasks.retry_payment_verification", max_retries=4, default_retry_delay=120)
def retry_payment_verification(payment_id: int) -> str:
    try:
        payment = Payment.objects.select_related("order").get(pk=payment_id)
    except Payment.DoesNotExist:
        return f"skipped:payment_not_found:{payment_id}"

    if payment.status == "completed":
        return f"already_completed:{payment.transaction_id}"

    sslcz = SSLCommerzPayment()
    response = sslcz.transaction_query_by_tran_id(payment.transaction_id)
    PaymentLog.objects.create(
        payment=payment,
        event_type="verification_retry",
        event_data=response if isinstance(response, dict) else {"raw": str(response)},
    )

    if response.get("status") in ["VALID", "VALIDATED"]:
        with transaction.atomic():
            payment.mark_as_completed()
        return f"verified:{payment.transaction_id}"

    if response.get("status") == "error":
        raise Exception(response.get("message", "verification error"))

    return f"not_verified:{payment.transaction_id}"


@shared_task(name="payments.tasks.reprocess_failed_callbacks")
def reprocess_failed_callbacks(batch_size: int = 20) -> str:
    failed = Payment.objects.filter(status__in=["failed", "processing"]).order_by("-updated_at")[:batch_size]
    queued = 0
    for payment in failed:
        retry_payment_verification.delay(payment.id)
        queued += 1
    return f"queued:{queued}"
