from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "property_slug", "checkin", "checkout", "guests", "total", "created_at")
    list_filter = ("property_slug", "created_at")
    search_fields = ("user__username", "first_name", "last_name", "email", "phone")
