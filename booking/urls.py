from django.urls import path

from .views import admin_dashboard, booking_success, create_booking, home, payment_view, signup_view


urlpatterns = [
    path("", home, name="home"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("signup/", signup_view, name="signup"),
    path("book/", create_booking, name="create_booking"),
    path("book/<int:booking_id>/payment/", payment_view, name="payment"),
    path("book/<int:booking_id>/success/", booking_success, name="booking_success"),
]
