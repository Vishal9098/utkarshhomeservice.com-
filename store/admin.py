from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
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
    list_display = ['order_id', 'name', 'phone', 'status', 'invoice_approved', 'created_at', 'whatsapp_delivery_button']
    list_editable = ['invoice_approved']
    list_filter = ['status', 'invoice_approved']
    search_fields = ['order_id', 'name', 'phone']

    def whatsapp_delivery_button(self, obj):
        # Delivery boy ka number — apna number yahan daalo
        DELIVERY_BOY_NUMBER = "919098535060"  # 91 + number (no + sign)

        # Share link banao
        order_id = obj.order_id.replace('#', '')
        share_link = f"https://utkarshhomeservice.com/delivery/share/{order_id}/"

        # WhatsApp message
        message = (
            f"🚴 *Naya Order Aaya Hai!*\n\n"
            f"📦 Order ID: {obj.order_id}\n"
            f"👤 Customer: {obj.name}\n"
            f"📞 Phone: {obj.phone}\n"
            f"📍 Address: {obj.address}, {obj.city}\n"
            f"📅 Date: {obj.service_date}\n"
            f"🕐 Time: {obj.service_time}\n\n"
            f"🔗 Tracking link lene ke liye ye kholo:\n"
            f"{share_link}\n\n"
            f"Jo link mile use customer track kar sakta hai."
        )

        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{DELIVERY_BOY_NUMBER}?text={encoded_message}"

        return format_html(
            '<a href="{}" target="_blank" style="'
            'background-color:#25D366; color:white; padding:5px 10px; '
            'border-radius:5px; text-decoration:none; font-weight:bold;'
            '">📱 WhatsApp</a>',
            whatsapp_url
        )

    whatsapp_delivery_button.short_description = "Delivery Boy"


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