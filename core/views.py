from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Listing, Booking, Profile, Category, ListingImage, Availability, Review, Message
from django.db.models import Q
from datetime import datetime, timedelta

def home(request):
    featured_listings = Listing.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'core/home.html', {'featured_listings': featured_listings})

def listing_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    max_price = request.GET.get('max_price')
    listings = Listing.objects.filter(is_available=True)

    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )
    if category_id:
        listings = listings.filter(category_id=category_id)
    if max_price:
        listings = listings.filter(price__lte=max_price)

    categories = Category.objects.all()
    return render(request, 'core/listing_list.html', {
        'listings': listings, 'query': query, 'categories': categories,
        'selected_category': category_id, 'max_price': max_price
    })

def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, 'core/listing_detail.html', {'listing': listing})

@login_required
def create_listing(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        category_id = request.POST['category']
        rental_type = request.POST['rental_type']
        price = request.POST['price']
        pricing_unit = request.POST['pricing_unit']
        location = request.POST['location']
        instant_book = request.POST.get('instant_book', False) == 'on'

        listing = Listing.objects.create(
            title=title,
            description=description,
            category_id=category_id,
            rental_type=rental_type,
            owner=request.user,
            price=price,
            pricing_unit=pricing_unit,
            location=location,
            instant_book=instant_book
        )

        images = request.FILES.getlist('images')
        for image in images:
            listing_image = ListingImage.objects.create(image=image)
            listing.images.add(listing_image)

        return redirect('dashboard')
    categories = Category.objects.all()
    return render(request, 'core/create_listing.html', {'categories': categories})

@login_required
def book_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        duration = (end - start).days  # In days for now, we’ll adjust below

        # Calculate total price based on pricing unit
        if listing.pricing_unit == 'hour':
            duration_hours = duration * 24
            total_price = listing.price * duration_hours
        elif listing.pricing_unit == 'day':
            total_price = listing.price * duration
        elif listing.pricing_unit == 'week':
            total_price = listing.price * (duration / 7)
        elif listing.pricing_unit == 'month':
            total_price = listing.price * (duration / 30)  # Approximate
        elif listing.pricing_unit == 'year':
            total_price = listing.price * (duration / 365)  # Approximate

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
            return render(request, 'core/book_listing.html', {
                'listing': listing,
                'availability': listing.availability.all(),
                'error': 'This listing is not available or already booked for the selected dates.'
            })

        booking = Booking.objects.create(
            listing=listing,
            renter=request.user,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status='pending' if not listing.instant_book else 'confirmed',
            payment_status='unpaid'
        )
        return redirect('dashboard')
    availability = listing.availability.all()
    return render(request, 'core/book_listing.html', {'listing': listing, 'availability': availability})

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'individual'}
    )
    owned_listings = Listing.objects.filter(owner=request.user)
    bookings_made = Booking.objects.filter(renter=request.user)
    bookings_received = Booking.objects.filter(listing__owner=request.user)
    total_revenue = sum(booking.total_price for booking in bookings_received if booking.status == 'confirmed' and booking.payment_status == 'paid')
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
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'individual'}
    )
    if request.method == 'POST':
        user_type = request.POST['user_type']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        profile.user_type = user_type
        profile.phone_number = phone_number
        profile.address = address
        profile.save()
        return redirect('dashboard')
    return render(request, 'core/profile_setup.html', {'profile': profile})

@login_required
def set_availability(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        return redirect('dashboard')
    if request.method == 'POST':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        Availability.objects.create(
            listing=listing,
            start_date=start_date,
            end_date=end_date
        )
        return redirect('dashboard')
    return render(request, 'core/set_availability.html', {'listing': listing})

@login_required
def pay_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)
    if request.method == 'POST':
        booking.payment_status = 'paid'
        if booking.status == 'confirmed':
            booking.status = 'confirmed'
        else:
            booking.status = 'pending'
        booking.save()
        return redirect('dashboard')
    return render(request, 'core/pay_booking.html', {'booking': booking})

@login_required
def leave_review(request, pk):
    booking = get_object_or_404(Booking, pk=pk, renter=request.user)
    if booking.status != 'confirmed' or booking.payment_status != 'paid' or booking.review.exists():
        return redirect('dashboard')
    if request.method == 'POST':
        rating = request.POST['rating']
        comment = request.POST['comment']
        Review.objects.create(
            booking=booking,
            rating=rating,
            comment=comment
        )
        return redirect('dashboard')
    return render(request, 'core/leave_review.html', {'booking': booking})

@login_required
def send_message(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        content = request.POST['content']
        Message.objects.create(
            sender=request.user,
            recipient=listing.owner,
            listing=listing,
            content=content
        )
        return redirect('dashboard')
    return render(request, 'core/send_message.html', {'listing': listing})

@login_required
def messages(request):
    sent_messages = Message.objects.filter(sender=request.user)
    received_messages = Message.objects.filter(recipient=request.user)
    return render(request, 'core/messages.html', {
        'sent_messages': sent_messages,
        'received_messages': received_messages
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Profile.objects.get_or_create(user=user, defaults={'user_type': 'individual'})
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})