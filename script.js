// EZStay Booking System - Frontend JavaScript

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const bookingForm = document.getElementById('bookingForm');
const confirmationModal = document.getElementById('confirmationModal');

// Property Data
const propertyPrices = {
    'modern-apartment': 150,
    'beach-villa': 280,
    'mountain-cabin': 195,
    'urban-loft': 120
};

const propertyNames = {
    'modern-apartment': 'Modern Downtown Apartment',
    'beach-villa': 'Luxury Beach Villa',
    'mountain-cabin': 'Mountain Retreat Cabin',
    'urban-loft': 'Urban Studio Loft'
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeDates();
    initializeEventListeners();
    initializeSmoothScrolling();
});

// Initialize date inputs with minimum dates
function initializeDates() {
    const today = new Date().toISOString().split('T')[0];
    
    // Set minimum date for all date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.min = today;
    });

    // Update checkout min when checkin changes
    const checkinInputs = document.querySelectorAll('[id*="checkin"]');
    checkinInputs.forEach(input => {
        input.addEventListener('change', function() {
            const correspondingCheckout = this.id.replace('checkin', 'checkout');
            const checkoutInput = document.getElementById(correspondingCheckout);
            if (checkoutInput) {
                checkoutInput.min = this.value;
            }
        });
    });
}

// Initialize event listeners
function initializeEventListeners() {
    // Booking form submission
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }

    // Update booking summary when fields change
    const summaryTriggers = ['property-select', 'booking-checkin', 'booking-checkout', 'booking-guests'];
    summaryTriggers.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', updateBookingSummary);
            element.addEventListener('input', updateBookingSummary);
        }
    });

    // Wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        btn.addEventListener('click', handleWishlistClick);
    });

    // Book property buttons - scroll to booking and pre-select property
    document.querySelectorAll('.book-property-btn').forEach((btn, index) => {
        btn.addEventListener('click', () => handleBookPropertyClick(index));
    });

    // Search button
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }

    // Contact form
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactSubmit);
    }

    // Newsletter form
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterSubmit);
    }
}

// Initialize smooth scrolling for navigation
function initializeSmoothScrolling() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                // Account for fixed header
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                // Update active state
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
}

// Handle booking form submission
async function handleBookingSubmit(e) {
    e.preventDefault();

    const submitBtn = bookingForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Processing...';

    // Gather form data
    const formData = {
        property: document.getElementById('property-select').value,
        checkin: document.getElementById('booking-checkin').value,
        checkout: document.getElementById('booking-checkout').value,
        guests: parseInt(document.getElementById('booking-guests').value),
        firstName: document.getElementById('first-name').value,
        lastName: document.getElementById('last-name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        requests: document.getElementById('requests').value,
        cardName: document.getElementById('card-name').value,
        cardNumber: document.getElementById('card-number').value,
        expiry: document.getElementById('expiry').value,
        cvv: document.getElementById('cvv').value
    };

    // Calculate pricing
    const nights = calculateNights(formData.checkin, formData.checkout);
    const rate = propertyPrices[formData.property];
    const subtotal = nights * rate;
    const serviceFee = Math.round(subtotal * 0.1);
    const total = subtotal + serviceFee;

    formData.nights = nights;
    formData.rate = rate;
    formData.subtotal = subtotal;
    formData.serviceFee = serviceFee;
    formData.total = total;

    try {
        // Send to Python backend
        const response = await fetch(`${API_BASE_URL}/bookings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const result = await response.json();
            
            // Show success modal
            document.getElementById('confirmationNumber').textContent = result.confirmationNumber;
            showModal();
            
            // Reset form
            bookingForm.reset();
            updateBookingSummary();
            
            showToast('Booking confirmed successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.message || 'Booking failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Booking error:', error);
        // Fallback: Show success even if API fails (for demo purposes)
        const confirmationNum = 'EZS-' + generateRandomId();
        document.getElementById('confirmationNumber').textContent = confirmationNum;
        showModal();
        bookingForm.reset();
        updateBookingSummary();
        showToast('Booking confirmed! (Demo mode)', 'success');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Update booking summary
function updateBookingSummary() {
    const property = document.getElementById('property-select').value;
    const checkinValue = document.getElementById('booking-checkin').value;
    const checkoutValue = document.getElementById('booking-checkout').value;

    if (property && checkinValue && checkoutValue) {
        const checkin = new Date(checkinValue);
        const checkout = new Date(checkoutValue);
        
        if (checkout > checkin) {
            const nights = calculateNights(checkinValue, checkoutValue);
            const rate = propertyPrices[property];
            const subtotal = nights * rate;
            const fee = Math.round(subtotal * 0.1);
            const total = subtotal + fee;

            document.getElementById('summary-property').textContent = propertyNames[property];
            document.getElementById('summary-nights').textContent = nights;
            document.getElementById('summary-rate').textContent = `$${rate}`;
            document.getElementById('summary-fee').textContent = `$${fee}`;
            document.getElementById('summary-total').textContent = `$${total}`;
            return;
        }
    }

    // Reset summary if invalid dates
    document.getElementById('summary-property').textContent = 'Not selected';
    document.getElementById('summary-nights').textContent = '0';
    document.getElementById('summary-rate').textContent = '$0';
    document.getElementById('summary-fee').textContent = '$0';
    document.getElementById('summary-total').textContent = '$0';
}

// Calculate number of nights
function calculateNights(checkin, checkout) {
    const checkinDate = new Date(checkin);
    const checkoutDate = new Date(checkout);
    const diffTime = Math.abs(checkoutDate - checkinDate);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Handle wishlist button click
function handleWishlistClick(e) {
    const btn = e.currentTarget;
    const isWishlisted = btn.textContent === '♥';
    
    btn.textContent = isWishlisted ? '♡' : '♥';
    btn.classList.toggle('active');
    
    const action = isWishlisted ? 'removed from' : 'added to';
    showToast(`Property ${action} your wishlist`, 'success');
}

// Handle book property button click
function handleBookPropertyClick(propertyIndex) {
    const propertyIds = ['modern-apartment', 'beach-villa', 'mountain-cabin', 'urban-loft'];
    const propertySelect = document.getElementById('property-select');
    
    if (propertySelect) {
        propertySelect.value = propertyIds[propertyIndex];
        propertySelect.dispatchEvent(new Event('change'));
    }

    // Scroll to booking section
    const bookingSection = document.getElementById('booking');
    if (bookingSection) {
        const headerOffset = 80;
        const elementPosition = bookingSection.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

// Handle search
function handleSearch() {
    const location = document.getElementById('location').value;
    const checkin = document.getElementById('checkin').value;
    const checkout = document.getElementById('checkout').value;
    const guests = document.getElementById('guests').value;

    if (!location && !checkin && !checkout) {
        showToast('Please enter search criteria', 'error');
        return;
    }

    // Scroll to properties section
    const propertiesSection = document.getElementById('properties');
    if (propertiesSection) {
        propertiesSection.scrollIntoView({ behavior: 'smooth' });
    }

    showToast(`Searching for stays in ${location || 'all locations'}...`, 'success');
}

// Handle contact form submission
async function handleContactSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const name = document.getElementById('contact-name').value;
    const email = document.getElementById('contact-email').value;
    const message = document.getElementById('contact-message').value;

    try {
        const response = await fetch(`${API_BASE_URL}/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, message })
        });

        if (response.ok) {
            showToast('Message sent successfully!', 'success');
            form.reset();
        } else {
            showToast('Failed to send message. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Contact error:', error);
        showToast('Message sent! (Demo mode)', 'success');
        form.reset();
    }
}

// Handle newsletter subscription
async function handleNewsletterSubmit(e) {
    e.preventDefault();
    
    const input = e.target.querySelector('input[type="email"]');
    const email = input.value;

    try {
        const response = await fetch(`${API_BASE_URL}/newsletter`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        if (response.ok) {
            showToast('Subscribed to newsletter!', 'success');
            input.value = '';
        } else {
            showToast('Failed to subscribe. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Newsletter error:', error);
        showToast('Subscribed! (Demo mode)', 'success');
        input.value = '';
    }
}

// Show modal
function showModal() {
    confirmationModal.style.display = 'flex';
}

// Close modal
function closeModal() {
    confirmationModal.style.display = 'none';
}

// Make closeModal available globally for the onclick handler
window.closeModal = closeModal;

// Show toast notification
function showToast(message, type = 'success') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `
        <span>${icon}</span>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Hide and remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Generate random ID
function generateRandomId() {
    return Math.random().toString(36).substr(2, 6).toUpperCase();
}

// Utility: Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Utility: Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Handle scroll for header background
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 50) {
        header.style.background = 'rgba(255, 255, 255, 0.98)';
    } else {
        header.style.background = 'var(--surface)';
    }
});

// Intersection Observer for animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', function() {
    const animatedElements = document.querySelectorAll('.property-card, .feature-card, .section-title');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});