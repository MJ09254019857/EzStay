from datetime import date
from decimal import Decimal
import base64
import json
import socket
from urllib import error as urlerror
from urllib import request as urlrequest
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SignUpForm
from .models import Booking


PROPERTY_RATES = {
    "april-rose": Decimal("300.00"),
    "beach-villa": Decimal("500.00"),
    "sunrise": Decimal("195.00"),
    "urban-loft": Decimal("120.00"),
    "riverside-garden": Decimal("350.00"),
}

# ============================================================
#  PAYMONGO INTEGRATION
# ============================================================

PAYMONGO_CHECKOUT_URL = "https://api.paymongo.com/v1/checkout_sessions"
_NO_PROXY_OPENER = urlrequest.build_opener(urlrequest.ProxyHandler({}))


def _paymongo_headers():
    """Build the Authorization header using the secret key from settings."""
    secret_key = settings.PAYMONGO_SECRET_KEY
    if not secret_key:
        return None
    encoded = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {encoded}",
    }


def _paymongo_create_checkout_session(booking):
    """
    Call the PayMongo Checkout Sessions API and return (checkout_url, reference_number).
    Shows all available payment methods (GCash, Maya, Card, QR Ph).
    """
    headers = _paymongo_headers()
    if not headers:
        raise RuntimeError("PAYMONGO_SECRET_KEY is missing.")

    amount_centavos = int((booking.total * 100).quantize(Decimal("1")))
    success_url = f"{settings.APP_BASE_URL}/book/{booking.id}/success/"
    cancel_url  = f"{settings.APP_BASE_URL}/book/{booking.id}/payment/"

    payload = {
        "data": {
            "attributes": {
                "line_items": [
                    {
                        "currency": "PHP",
                        "amount": amount_centavos,
                        "name": f"EZStay Booking #{booking.id}",
                        "quantity": 1,
                    }
                ],
                # ✅ ALL payment methods — PayMongo will show whichever are available
                "payment_method_types": ["gcash", "paymaya", "card", "qrph"],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "description": f"Booking for {booking.get_property_slug_display()}",
                "metadata": {
                    "booking_id": str(booking.id),
                    "user_id": str(booking.user_id),
                },
            }
        }
    }

    req = urlrequest.Request(
        PAYMONGO_CHECKOUT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    attempts = 2
    last_error = None
    for _ in range(attempts):
        try:
            with _NO_PROXY_OPENER.open(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
                attrs = data.get("data", {}).get("attributes", {})
                checkout_url = attrs.get("checkout_url")
                reference_number = attrs.get("reference_number", "")
                if not checkout_url:
                    raise RuntimeError("PayMongo checkout URL was not returned.")
                return checkout_url, reference_number
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"PayMongo API error ({exc.code}): {body}")
        except (urlerror.URLError, socket.gaierror) as exc:
            last_error = exc

    reason = getattr(last_error, "reason", last_error)
    raise RuntimeError(f"Could not reach PayMongo: {reason}")

# ============================================================
#  VIEWS
# ============================================================

def home(request):
    return render(request, "booking/home.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to EZStay! Your account has been created.")
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def create_booking(request):
    if request.method != "POST":
        return redirect("home")

    property_slug = request.POST.get("property_slug", "")
    checkin_raw   = request.POST.get("checkin", "")
    checkout_raw  = request.POST.get("checkout", "")

    try:
        checkin  = date.fromisoformat(checkin_raw)
        checkout = date.fromisoformat(checkout_raw)
    except ValueError:
        messages.error(request, "Please provide valid check-in and check-out dates.")
        return redirect("home")

    if property_slug not in PROPERTY_RATES:
        messages.error(request, "Please select a valid property.")
        return redirect("home")

    if checkout <= checkin:
        messages.error(request, "Check-out date must be after check-in date.")
        return redirect("home")

    nights      = (checkout - checkin).days
    rate        = PROPERTY_RATES[property_slug]
    subtotal    = rate * nights
    service_fee = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    total       = subtotal + service_fee

    booking = Booking.objects.create(
        user=request.user,
        property_slug=property_slug,
        checkin=checkin,
        checkout=checkout,
        guests=int(request.POST.get("guests", 1)),
        first_name=request.POST.get("first_name", "").strip(),
        last_name=request.POST.get("last_name", "").strip(),
        email=request.POST.get("email", "").strip(),
        phone=request.POST.get("phone", "").strip(),
        requests=request.POST.get("requests", "").strip(),
        nights=nights,
        rate=rate,
        service_fee=service_fee,
        total=total,
    )

    messages.success(request, "Booking details saved. Please complete payment to confirm your reservation.")
    return redirect("payment", booking_id=booking.id)


@login_required
def payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.is_paid:
        messages.info(request, "This booking has already been paid.")
        return redirect("booking_success", booking_id=booking.id)

    if request.method == "POST":
        # ✅ No need to pick payment method — PayMongo shows all options
        try:
            checkout_url, reference_number = _paymongo_create_checkout_session(booking)
            if reference_number:
                booking.payment_reference = reference_number
                booking.save(update_fields=["payment_reference"])
            return redirect(checkout_url)
        except RuntimeError as exc:
            messages.error(request, f"Unable to start PayMongo checkout. {exc}")
            return redirect("payment", booking_id=booking.id)

    return render(request, "booking/payment.html", {"booking": booking})


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if not booking.is_paid:
        booking.is_paid = True
        if not booking.payment_reference:
            booking.payment_reference = f"PAYMONGO-{uuid4().hex[:10].upper()}"
        booking.save(update_fields=["is_paid", "payment_reference"])

    return render(request, "booking/booking_success.html", {"booking": booking})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to access the admin dashboard.")
        return redirect("home")

    bookings       = Booking.objects.select_related("user")
    total_bookings = bookings.count()
    paid_bookings  = bookings.filter(is_paid=True).count()
    unpaid_bookings = total_bookings - paid_bookings
    total_revenue  = bookings.filter(is_paid=True).aggregate(total=Sum("total"))["total"] or Decimal("0.00")

    property_breakdown = (
        bookings.values("property_slug")
        .annotate(total=Count("id"), paid=Count("id", filter=Q(is_paid=True)))
        .order_by("-total")
    )

    property_labels = dict(Booking.PROPERTY_CHOICES)
    for row in property_breakdown:
        row["property_name"] = property_labels.get(row["property_slug"], row["property_slug"])

    recent_bookings = bookings.order_by("-created_at")[:10]

    return render(
        request,
        "booking/admin_dashboard.html",
        {
            "total_bookings":    total_bookings,
            "paid_bookings":     paid_bookings,
            "unpaid_bookings":   unpaid_bookings,
            "total_revenue":     total_revenue,
            "property_breakdown": property_breakdown,
            "recent_bookings":   recent_bookings,
        },
    )