from django.db import models
from django.contrib.auth.models import User


class Booking(models.Model):
    PROPERTY_CHOICES = [
        ("april-rose", "APRIL ROSE LODGING HOUSE"),
        ("beach-villa", "Luxury Beach Villa"),
        ("sunrise", "SUNRISE LODGING"),
        ("urban-loft", "Urban Studio Loft"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    property_slug = models.CharField(max_length=50, choices=PROPERTY_CHOICES)
    checkin = models.DateField()
    checkout = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    requests = models.TextField(blank=True)

    nights = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_property_slug_display()} ({self.checkin} to {self.checkout})"
