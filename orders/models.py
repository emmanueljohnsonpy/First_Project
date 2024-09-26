from django.db import models
from store.models import Product
from accounts.models import Account
import random
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'), 
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Return Request', 'Return Request'), 
        ('Return Pending', 'Return Pending'),
        ('Return Cancelled', 'Return Cancelled'),
        ('Return Success', 'Return Success'),
        ('Payment Pending', 'Payment Pending')
    ]
    address_line1 = models.CharField(max_length=255, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=100, null=True)
    pincode = models.CharField(max_length=20, null=True)
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, null=True, blank=True)  # New field for name
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Total price
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=50)  
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', null=True)
    payment_method = models.CharField(max_length=50, null=True)
    email = models.EmailField(null=True)  # Store user's email
    created_at = models.DateTimeField(auto_now_add=True, null=True)  # Date and time of order creation
    updated_at = models.DateTimeField(auto_now=True, null=True)
    order_number = models.CharField(max_length=6, unique=True, null=True, blank=True)  # New field for order number
    is_ordered = models.BooleanField(default=False)
    coupon_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    coupon_id = models.IntegerField(null=True, blank=True)  # New field for coupon ID applied
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username if self.user else 'Anonymous'}"

    def get_status_choices(self):
        return self.STATUS_CHOICES

    def generate_unique_order_number(self):
        """Generate a unique 6-digit order number."""
        while True:
            order_number = str(random.randint(100000, 999999))
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(null=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"
from django.db import models

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', null=True)
    payment_method = models.CharField(max_length=50, null=True)
    payment_status = models.CharField(max_length=20, default='Pending', null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    # New fields for Razorpay integration
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"

    def save(self, *args, **kwargs):
        # Optionally add custom save logic here
        super(Payment, self).save(*args, **kwargs)


class Coupon(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    )

    ACTION_CHOICES = (
        ('block', 'Block'),
        ('unblock', 'Unblock'),
    )

    code = models.CharField(max_length=20, unique=True, verbose_name="Coupon Code")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Discount Percentage")
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Minimum Purchase Amount")
    max_redeemable_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Max Redeemable Value", null=True)  # New field
    quantity = models.PositiveIntegerField(verbose_name="Quantity", null=True)
    expiry_date = models.DateField(verbose_name="Expiry Date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='block', verbose_name="Action")

    def __str__(self):
        return self.code


class Wallet(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('transfer', 'Transfer'),
        ('cash', 'Cash'),
    ]
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='wallet')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    def update_balance(self, transaction_type, amount):
        amount = Decimal(str(amount))   # Ensure amount is a Decimal
        if transaction_type == 'credit':
            self.wallet_balance += amount
        elif transaction_type == 'debit':
            self.wallet_balance -= amount
        self.save()

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=Wallet.PAYMENT_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username}'s {self.transaction_type} - {self.amount}"


class ReferralOffer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_offers', null=True, blank=True)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the referral offer.")
    description = models.TextField(help_text="Description of the referral offer.", null=True)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of reward for the referral.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the offer is currently active.")
    start_date = models.DateTimeField(default=timezone.now, help_text="Start date of the offer.", null=True)
    end_date = models.DateTimeField(null=True, blank=True, help_text="End date of the offer.")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of times the offer can be used.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the offer was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the offer was last updated.")

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Referral Offer"
        verbose_name_plural = "Referral Offers"
        ordering = ['-start_date']



class OrderedItems(models.Model):
    order_number = models.CharField(max_length=6, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=50)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=50) 

    def save(self, *args, **kwargs):
        self.total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number}, {self.product}, {self.unit_price}, {self.quantity}, {self.size}"