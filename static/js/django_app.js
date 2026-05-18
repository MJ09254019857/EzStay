document.addEventListener('DOMContentLoaded', function () {
    const propertySelect = document.getElementById('property-select');
    const checkinInput = document.getElementById('booking-checkin');
    const checkoutInput = document.getElementById('booking-checkout');

    const propertyRates = {
        'april-rose': 300,
        'beach-villa': 500,
        'sunrise': 195,
        'urban-loft': 120,
        'riverside-garden': 350
    };

    const propertyNames = {
        'april-rose': 'APRIL ROSE LODGING HOUSE',
        'beach-villa': 'Luxury Beach Villa',
        'sunrise': 'SUNRISE LODGING',
        'urban-loft': 'Urban Studio Loft',
        'riverside-garden': 'Riverside Garden Inn'
    };

    const today = new Date().toISOString().split('T')[0];
    if (checkinInput) checkinInput.min = today;
    if (checkoutInput) checkoutInput.min = today;

    if (checkinInput && checkoutInput) {
        checkinInput.addEventListener('change', function () {
            checkoutInput.min = this.value || today;
            if (checkoutInput.value && checkoutInput.value <= this.value) {
                checkoutInput.value = '';
            }
            updateSummary();
        });
    }

    [propertySelect, checkoutInput].forEach((el) => {
        if (el) {
            el.addEventListener('change', updateSummary);
            el.addEventListener('input', updateSummary);
        }
    });

    document.querySelectorAll('.book-property-btn').forEach((btn) => {
        btn.addEventListener('click', function () {
            const prop = this.dataset.property;
            if (propertySelect) {
                propertySelect.value = prop;
                updateSummary();
            }
            const bookingSection = document.getElementById('booking');
            if (bookingSection) {
                bookingSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    function updateSummary() {
        const property = propertySelect ? propertySelect.value : '';
        const checkin = checkinInput ? checkinInput.value : '';
        const checkout = checkoutInput ? checkoutInput.value : '';

        const summaryProperty = document.getElementById('summary-property');
        const summaryNights = document.getElementById('summary-nights');
        const summaryRate = document.getElementById('summary-rate');
        const summaryFee = document.getElementById('summary-fee');
        const summaryTotal = document.getElementById('summary-total');

        if (!summaryProperty || !summaryNights || !summaryRate || !summaryFee || !summaryTotal) return;

        if (!property || !checkin || !checkout) {
            summaryProperty.textContent = 'Not selected';
            summaryNights.textContent = '0';
            summaryRate.textContent = '0';
            summaryFee.textContent = '0';
            summaryTotal.textContent = '0';
            return;
        }

        const inDate = new Date(checkin);
        const outDate = new Date(checkout);
        const diffTime = outDate - inDate;
        const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (nights <= 0) {
            summaryNights.textContent = '0';
            summaryFee.textContent = '0';
            summaryTotal.textContent = '0';
            return;
        }

        const rate = propertyRates[property] || 0;
        const subtotal = nights * rate;
        const fee = Math.round(subtotal * 0.1);
        const total = subtotal + fee;

        summaryProperty.textContent = propertyNames[property] || 'Not selected';
        summaryNights.textContent = String(nights);
        summaryRate.textContent = String(rate);
        summaryFee.textContent = String(fee);
        summaryTotal.textContent = String(total);
    }

    updateSummary();
});