from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import logging
from .models import Listing, Booking, Profile, Category, ListingImage, Availability, Review, Message
from .forms import ListingForm, BookingForm, ProfileForm, AvailabilityForm, ReviewForm, MessageForm

# Set up logging
logger = logging.getLogger(__name__)

# Utility function for price calculation
def calculate_total_price(listing, start_date, end_date):
    """Calculate total price based on pricing unit and duration."""
    duration_days = (end_date - start_date).days
    if duration_days <= 0:
        raise ValidationError("End date must be after start date.")
    
    # Convert Decimal price to float for calculation, then back to Decimal
    price = float(listing.price)
    if listing.pricing_unit == 'hour':
        total_price = price * (duration_days * 24)
    elif listing.pricing_unit == 'day':
        total_price = price * duration_days
    elif listing.pricing_unit == 'week':
        total_price = price * (duration_days / 7)
    elif listing.pricing_unit == 'month':
        total_price = price * (duration_days / 30)
    elif listing.pricing_unit == 'year':
        total_price = price * (duration_days / 365)
    return round(total_price, 2)  # Match DecimalField decimal_places=2

def home(request):
    """Display featured listings on the homepage."""
    featured_listings = Listing.objects.filter(is_available=True).select_related('category').prefetch_related('images').order_by('-created_at')[:6]
    return render(request, 'core/home.html', {'featured_listings': featured_listings})

def listing_list(request):
    """List all available listings with filters."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    max_price = request.GET.get('max_price', '')

    listings = Listing.objects.filter(is_available=True).select_related('category').prefetch_related('images')

    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )
    if category_id.isdigit():
        listings = listings.filter(category_id=category_id)
    if max_price.replace('.', '', 1).isdigit():  # Allow decimal input
        listings = listings.filter(price__lte=float(max_price))

    categories = Category.objects.all()
    context = {
        'listings': listings,
        'query': query,
        'categories': categories,
        'selected_category': category_id,
        'max_price': max_price,
    }
    return render(request, 'core/listing_list.html', context)

def listing_detail(request, pk):
    """Display details of a specific listing."""
    listing = get_object_or_404(Listing.objects.select_related('category', 'owner').prefetch_related('images', 'availability', 'bookings__review'), pk=pk)
    return render(request, 'core/listing_detail.html', {'listing': listing})

@login_required
def create_listing(request):
    """Create a new listing with validation and multiple image uploads."""
    if request.method == 'POST':
        form = ListingForm(request.POST)  # No request.FILES here since images isn't in the form
        if form.is_valid():
            try:
                with transaction.atomic():
                    listing = form.save(commit=False)
                    listing.owner = request.user
                    listing.save()
                    
                    # Handle multiple image uploads directly from request.FILES
                    images = request.FILES.getlist('images')
                    for image in images:
                        ListingImage.objects.create(listing=listing, image=image)
                    
                    messages.success(request, "Listing created successfully!")
                    logger.info(f"User {request.user.id} created listing {listing.id}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Failed to create listing: {str(e)}")
                logger.error(f"Error creating listing for user {request.user.id}: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ListingForm()
    
    categories = Category.objects.all()  # For template compatibility
    return render(request, 'core/create_listing.html', {'form': form, 'categories': categories})

@login_required
def book_listing(request, pk):
    """Book a listing with security and availability checks."""
    listing = get_object_or_404(Listing.objects.select_related('owner'), pk=pk)
    
    if listing.owner == request.user:
        messages.error(request, "You cannot book your own listing.")
        return redirect('listing_detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Validate dates
            if start_date < timezone.now().date():
                messages.error(request, "Start date cannot be in the past.")
                return render(request, 'core/book_listing.html', {'listing': listing, 'form': form})
            
            try:
                total_price = calculate_total_price(listing, start_date, end_date)
                available = listing.availability.filter(
                    start_date__lte=end_date, end_date__gte=start_date
                ).exists()
                conflicting_booking = Booking.objects.filter(
                    listing=listing,
                    status__in=['pending', 'confirmed'],
                    start_date__lte=end_date,
                    end_date__gte=start_date
                ).exists()

                if not available or conflicting_booking:
                    messages.error(request, "This listing is not available for the selected dates.")
                    return render(request, 'core/book_listing.html', {'listing': listing, 'form': form})

                with transaction.atomic():
                    booking = Booking.objects.create(
                        listing=listing,
                        renter=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        total_price=total_price,
                        status='confirmed' if listing.instant_book else 'pending',
                        payment_status='unpaid'
                    )
                    messages.success(request, "Booking request submitted successfully!")
                    logger.info(f"User {request.user.id} booked listing {listing.id}")
                    return redirect('dashboard')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "An error occurred while booking.")
                logger.error(f"Error booking listing {listing.id} by user {request.user.id}: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BookingForm()

    availability = listing.availability.all()
    return render(request, 'core/book_listing.html', {'listing': listing, 'form': form, 'availability': availability})

@login_required
def dashboard(request):
    """Display user dashboard with optimized queries."""
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'user_type': 'individual'})
    
    owned_listings = Listing.objects.filter(owner=request.user).select_related('category').prefetch_related('images')
    bookings_made = Booking.objects.filter(renter=request.user).select_related('listing__category')
    bookings_received = Booking.objects.filter(listing__owner=request.user).select_related('renter', 'listing__category')
    
    revenue_data = bookings_received.filter(status='confirmed', payment_status='paid').aggregate(total=Sum('total_price'))
    total_revenue = revenue_data['total'] or 0
    total_bookings = bookings_received.count()
    pending_bookings = bookings_received.filter(status='pending').count()

    context = {
        'profile': profile,
        'owned_listings': owned_listings,
        'bookings_made': bookings_made,
        'bookings_received': bookings_received,
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def profile_setup(request):
    """Update user profile with form validation."""
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'user_type': 'individual'})
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'core/profile_setup.html', {'form': form})

@login_required
def set_availability(request, pk):
    """Set availability for a listing with ownership check."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.owner != request.user:
        messages.error(request, "You can only set availability for your own listings.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    availability = form.save(commit=False)
                    availability.listing = listing
                    availability.save()
                    messages.success(request, "Availability set successfully!")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Failed to set availability: {str(e)}")
                logger.error(f"Error setting availability for listing {listing.id}: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AvailabilityForm()
    
    return render(request, 'core/set_availability.html', {'listing': listing, 'form': form})

@login_required
def pay_booking(request, pk):
    """Process payment for a booking with security checks."""
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)
    if booking.listing.owner == request.user:
        messages.error(request, "You cannot pay for your own listing.")
        return redirect('dashboard')
    if booking.payment_status != 'unpaid':
        messages.error(request, "This booking is already paid or refunded.")
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                booking.payment_status = 'paid'
                booking.save()
                messages.success(request, "Payment processed successfully!")
                logger.info(f"User {request.user.id} paid for booking {booking.id}")
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, "Payment failed. Please try again.")
            logger.error(f"Error processing payment for booking {booking.id}: {str(e)}")
    
    return render(request, 'core/pay_booking.html', {'booking': booking})

@login_required
def leave_review(request, pk):
    """Leave a review for a confirmed, paid booking."""
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)
    if booking.status != 'confirmed' or booking.payment_status != 'paid' or booking.review.exists():
        messages.error(request, "You can only review confirmed and paid bookings once.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    review = form.save(commit=False)
                    review.booking = booking
                    review.save()
                    messages.success(request, "Review submitted successfully!")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Failed to submit review: {str(e)}")
                logger.error(f"Error submitting review for booking {booking.id}: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm()
    
    return render(request, 'core/leave_review.html', {'booking': booking, 'form': form})

@login_required
def send_message(request, pk):
    """Send a message to a listing owner."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.owner == request.user:
        messages.error(request, "You cannot send a message to yourself.")
        return redirect('listing_detail', pk=pk)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    message = form.save(commit=False)
                    message.sender = request.user
                    message.recipient = listing.owner
                    message.listing = listing
                    message.save()
                    messages.success(request, "Message sent successfully!")
                    logger.info(f"User {request.user.id} sent message to {listing.owner.id}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")
                logger.error(f"Error sending message for listing {listing.id}: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MessageForm()
    
    return render(request, 'core/send_message.html', {'listing': listing, 'form': form})

@login_required
def messages(request):
    """Display sent and received messages."""
    sent_messages = Message.objects.filter(sender=request.user).select_related('recipient', 'listing')
    received_messages = Message.objects.filter(recipient=request.user).select_related('sender', 'listing')
    return render(request, 'core/messages.html', {
        'sent_messages': sent_messages,
        'received_messages': received_messages
    })

def signup(request):
    """Handle user signup with profile creation."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    Profile.objects.create(user=user, user_type='individual')
                    login(request, user)
                    messages.success(request, "Account created successfully!")
                    logger.info(f"New user signed up: {user.id}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Signup failed: {str(e)}")
                logger.error(f"Error during signup: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    
    return render(request, 'core/signup.html', {'form': form})