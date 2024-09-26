from django.contrib import admin
from .models import Product, ReviewRating, ProductGallery, Offer
import admin_thumbnails


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline]

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

class OfferAdmin(admin.ModelAdmin):
    list_display = ('offer_name', 'offer_type', 'offer_percentage', 'status', 'action', 'created_at', 'updated_at')
    list_filter = ('offer_type', 'status', 'action')
    search_fields = ('offer_name', 'description')
    filter_horizontal = ('products', 'categories')

admin.site.register(Product, ProductAdmin)
# admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
admin.site.register(Offer, OfferAdmin)