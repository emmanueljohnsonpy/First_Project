from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
# Create your models here.

class Product(models.Model):
    product_name    = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True)
    description     = models.TextField(max_length=1000, blank=True)
    price           = models.IntegerField(null=True)
    images          = models.ImageField(upload_to='photos/products', null=True)
    image1 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    image2 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    stock_small = models.IntegerField(default=0)
    stock_medium = models.IntegerField(default=0)
    stock_large = models.IntegerField(default=0)
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)
    # size            = models.IntegerField(null=True)
    wishlisted      = models.BooleanField(default=False)
    wishlist_count  = models.PositiveIntegerField(default=0)
    wishlist_added_date = models.DateTimeField(null=True, blank=True)
    old_price       = models.IntegerField(null=True, blank=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    product_disc_added = models.BooleanField(default=False, null=True)
    cat_disc_added = models.BooleanField(default=False, null=True)
   
    
    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
    
    def get_total_stock(self):
        return self.stock_small + self.stock_medium + self.stock_large

        # Model-level validation to ensure stock doesn't go below 0
    def clean(self):
        if self.stock_small < 0:
            raise ValidationError('Stock for small size cannot be less than 0.')
        if self.stock_medium < 0:
            raise ValidationError('Stock for medium size cannot be less than 0.')
        if self.stock_large < 0:
            raise ValidationError('Stock for large size cannot be less than 0.')

    def save(self, *args, **kwargs):
    # Ensure price is calculated correctly based on old_price and discount_percentage
        if self.old_price is not None:
            if self.discount_percentage and self.discount_percentage > 0:
                discount_amount = (self.old_price * self.discount_percentage) / 100
                self.price = self.old_price - discount_amount
            else:
                self.price = self.old_price  # No discount applied
            
        self.clean()
        super(Product, self).save(*args, **kwargs)


    # def save(self, *args, **kwargs):
    #     # Calculate the price based on old_price and discount_percentage
    #     if self.old_price and self.discount_percentage:
    #         discount_amount = (self.old_price * self.discount_percentage) / 100
    #         self.price = self.old_price - discount_amount
    #     super(Product, self).save(*args, **kwargs)

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject
    


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery' 


from django.utils import timezone
from store.models import Product  # Import the Product model
from category.models import Category  # Import the Category model

class Offer(models.Model):
    OFFER_TYPE_CHOICES = [
        ('product', 'Product'),
        ('category', 'Category'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    OFFER_ACTION_CHOICES = [
        ('block', 'Block'),
        ('unblock', 'Unblock'),
    ]

    offer_name = models.CharField(max_length=255)
    description = models.TextField()
    offer_type = models.CharField(max_length=50, choices=OFFER_TYPE_CHOICES)
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    action = models.CharField(max_length=50, choices=OFFER_ACTION_CHOICES, default='unblock')
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.offer_name
