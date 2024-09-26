from django.contrib import admin
from .models import Order, OrderItem, Payment, Coupon, Wallet, WalletTransaction, ReferralOffer

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # No extra empty fields for new OrderItems
    readonly_fields = ('product', 'quantity', 'sub_total')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'tax', 'grand_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__username', 'status')
    inlines = [OrderItemInline]  # Display OrderItems inline in the Order admin page
    readonly_fields = ('total_price', 'tax', 'grand_total', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'payment_method')
        }),
        ('Financials', {
            'fields': ('total_price', 'tax', 'grand_total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_balance')

class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'description', 'date')
    list_filter = ('transaction_type', 'date')
    search_fields = ('wallet__user__username', 'transaction_type')

@admin.register(ReferralOffer)
class ReferralOfferAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'reward_amount', 'is_active', 'start_date', 'end_date', 'usage_limit', 'created_at', 'updated_at')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('code', 'description')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)