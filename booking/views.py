from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SignUpForm
from .models import Booking


PROPERTY_RATES = {
    "april-rose": Decimal("300.00"),
    "beach-villa": Decimal("500.00"),
    "sunrise": Decimal("195.00"),
    "urban-loft": Decimal("120.00"),
}


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
    checkin_raw = request.POST.get("checkin", "")
    checkout_raw = request.POST.get("checkout", "")

    try:
        checkin = date.fromisoformat(checkin_raw)
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

    nights = (checkout - checkin).days
    rate = PROPERTY_RATES[property_slug]
    subtotal = rate * nights
    service_fee = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    total = subtotal + service_fee

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
    payment_methods = ["gcash", "maya", "card"]

    if booking.is_paid:
        messages.info(request, "This booking has already been paid.")
        return redirect("booking_success", booking_id=booking.id)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "").strip().lower()

        if payment_method not in payment_methods:
            messages.error(request, "Please select a valid payment method.")
            return redirect("payment", booking_id=booking.id)

        if payment_method in ("gcash", "maya"):
            wallet_number = request.POST.get("wallet_number", "").replace(" ", "")
            if not wallet_number.isdigit() or len(wallet_number) != 11 or not wallet_number.startswith("09"):
                messages.error(request, "Please enter a valid mobile wallet number (e.g., 09XXXXXXXXX).")
                return redirect("payment", booking_id=booking.id)

        if payment_method == "card":
            card_name = request.POST.get("card_name", "").strip()
            card_number = request.POST.get("card_number", "").replace(" ", "")
            expiry = request.POST.get("expiry", "").strip()
            cvv = request.POST.get("cvv", "").strip()

            if not card_name or len(card_name) < 3:
                messages.error(request, "Please enter the cardholder name.")
                return redirect("payment", booking_id=booking.id)

            if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
                messages.error(request, "Please enter a valid card number.")
                return redirect("payment", booking_id=booking.id)

            if len(expiry) != 5 or expiry[2] != "/":
                messages.error(request, "Expiry format must be MM/YY.")
                return redirect("payment", booking_id=booking.id)

            mm, yy = expiry.split("/")
            if not (mm.isdigit() and yy.isdigit() and 1 <= int(mm) <= 12):
                messages.error(request, "Please enter a valid expiry date.")
                return redirect("payment", booking_id=booking.id)

            if not cvv.isdigit() or len(cvv) not in (3, 4):
                messages.error(request, "Please enter a valid CVV.")
                return redirect("payment", booking_id=booking.id)

        booking.is_paid = True
        booking.payment_reference = f"{payment_method.upper()}-{uuid4().hex[:10].upper()}"
        booking.save(update_fields=["is_paid", "payment_reference"])

        messages.success(request, f"Payment successful! Reference: {booking.payment_reference}")
        return redirect("booking_success", booking_id=booking.id)

    return render(request, "booking/payment.html", {"booking": booking})


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if not booking.is_paid:
        messages.warning(request, "Please complete payment to confirm this booking.")
        return redirect("payment", booking_id=booking.id)

    return render(request, "booking/booking_success.html", {"booking": booking})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to access the admin dashboard.")
        return redirect("home")

    bookings = Booking.objects.select_related("user")
    total_bookings = bookings.count()
    paid_bookings = bookings.filter(is_paid=True).count()
    unpaid_bookings = total_bookings - paid_bookings
    total_revenue = bookings.filter(is_paid=True).aggregate(total=Sum("total"))["total"] or Decimal("0.00")

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
            "total_bookings": total_bookings,
            "paid_bookings": paid_bookings,
            "unpaid_bookings": unpaid_bookings,
            "total_revenue": total_revenue,
            "property_breakdown": property_breakdown,
            "recent_bookings": recent_bookings,
        },
    )
