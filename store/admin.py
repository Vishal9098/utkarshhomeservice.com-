from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Service)
admin.site.register(ServiceImage)
admin.site.register(Coupon)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Blog)
admin.site.register(Gallery)
admin.site.register(ContactQuery)
admin.site.register(Testimonial)
admin.site.register(UserProfile)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'name', 'status', 'invoice_approved', 'created_at']
    list_editable = ['invoice_approved']
    list_filter = ['status', 'invoice_approved']
    search_fields = ['order_id', 'name', 'phone']