from django.db import models
from orders.models import Order
from accounts.models import CustomUser


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('sslcommerz', 'SSL Commerce'),
        ('card', 'Credit/Debit Card'),
        ('mobile_banking', 'Mobile Banking'),
        ('internet_banking', 'Internet Banking'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    
    # Payment Details
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    
    # SSL Commerce Specific Fields
    val_id = models.CharField(max_length=100, blank=True, null=True)  # Validation ID from SSL
    card_type = models.CharField(max_length=50, blank=True, null=True)
    card_no = models.CharField(max_length=20, blank=True, null=True)  # Last 4 digits
    bank_tran_id = models.CharField(max_length=100, blank=True, null=True)
    card_issuer = models.CharField(max_length=100, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_issuer_country = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional Information
    risk_level = models.CharField(max_length=20, blank=True, null=True)
    risk_title = models.CharField(max_length=100, blank=True, null=True)
    
    # Response Data
    response_data = models.JSONField(blank=True, null=True)  # Store full response
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.get_status_display()}"
    
    def is_successful(self):
        return self.status == 'completed'
    
    def mark_as_completed(self):
        """Mark payment as completed and update order"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # FIX: order.payment_status is now a CharField ('paid'), not a boolean
        self.order.payment_status = 'paid'
        self.order.order_status = 'processing'
        self.order.save()
    
    def mark_as_failed(self, error_message=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()


class PaymentLog(models.Model):
    """Log all payment activities for debugging and auditing"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)  # initiated, ipn_received, validated, etc.
    event_data = models.JSONField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment.transaction_id} - {self.event_type}"