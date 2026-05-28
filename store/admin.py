from django.contrib import admin
from django.utils.html import format_html
from .models import *

admin.site.register(Category)
admin.site.register(Service)
admin.site.register(ServiceImage)
admin.site.register(Coupon)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Blog)
admin.site.register(Gallery)
admin.site.register(ContactQuery)
admin.site.register(Testimonial)
admin.site.register(UserProfile)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['service', 'quantity', 'price', 'get_total']
    fields = ['service', 'quantity', 'price', 'get_total']

    def get_total(self, obj):
        try:
            if obj.price is not None:
                return f"₹{obj.quantity * obj.price:.2f}"
            return "₹0.00"
        except:
            return "₹0.00"
    get_total.short_description = "Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'name', 'phone', 'status', 'invoice_approved', 'created_at']
    list_editable = ['invoice_approved']
    list_filter = ['status', 'invoice_approved']
    search_fields = ['order_id', 'name', 'phone']
    inlines = [OrderItemInline]


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 1
    fields = ['status', 'message', 'updated_by']


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_at']


@admin.register(DeliveryLocation)
class DeliveryLocationAdmin(admin.ModelAdmin):
    list_display = ['order', 'latitude', 'longitude', 'dest_latitude', 'dest_longitude', 'is_active', 'updated_at']