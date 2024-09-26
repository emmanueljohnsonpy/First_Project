from django.db import models
from store.models import Product
from accounts.models import Account

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True, unique=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

    def total_price(self):
        items = CartItem.objects.filter(cart=self, is_active=True)
        return sum(item.sub_total() for item in items)

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    size = models.CharField(max_length=20, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.product_name} (x{self.quantity})"

from django.db import models
from django.contrib.auth.models import User
from orders.models import Coupon

class CheckoutDetails(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=50)  
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    coupon_applied = models.BooleanField(default=False, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_key_id = models.CharField(max_length=255, null=True, blank=True)
    before_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='checkout_details', null=True) 
    
    def __str__(self):
        return f"Checkout by {self.user.username} on {self.created_at}"
