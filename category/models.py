from django.db import models
from django.urls import reverse

# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    status = models.CharField(max_length=100, default=True)
    is_available    = models.BooleanField(default=True)
    offer_added = models.BooleanField(default=False, null=True)
    # ForeignKey defined but imported inside the method
    applied_offer = models.ForeignKey(
        'store.Offer',  # Use string notation to reference the Offer model
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    applied_offer_name = models.CharField(max_length=20 ,null=True)
    applied_offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural ='categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name
    

