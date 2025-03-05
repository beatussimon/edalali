from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Listing, Booking, Profile, Category
from django.db.models import Q
from datetime import datetime

def home(request):
    featured_listings = Listing.objects.filter(is_available=True).order_by('-created_at')[:6]
    return render(request, 'core/home.html', {'featured_listings': featured_listings})

def listing_list(request):
    query = request.GET.get('q', '')
    listings = Listing.objects.filter(is_available=True)
    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )
    return render(request, 'core/listing_list.html', {'listings': listings, 'query': query})

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
        price_per_day = request.POST['price_per_day']
        location = request.POST['location']
        instant_book = request.POST.get('instant_book', False) == 'on'

        listing = Listing.objects.create(
            title=title,
            description=description,
            category_id=category_id,
            rental_type=rental_type,
            owner=request.user,
            price_per_day=price_per_day,
            location=location,
            instant_book=instant_book
        )
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
        days = (end - start).days
        total_price = listing.price_per_day * days

        booking = Booking.objects.create(
            listing=listing,
            renter=request.user,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status='pending' if not listing.instant_book else 'confirmed'
        )
        return redirect('dashboard')
    return render(request, 'core/book_listing.html', {'listing': listing})

@login_required
def dashboard(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect('profile_setup')

    owned_listings = Listing.objects.filter(owner=request.user)
    bookings_made = Booking.objects.filter(renter=request.user)
    bookings_received = Booking.objects.filter(listing__owner=request.user)
    total_revenue = sum(booking.total_price for booking in bookings_received if booking.status == 'confirmed')

    context = {
        'profile': profile,
        'owned_listings': owned_listings,
        'bookings_made': bookings_made,
        'bookings_received': bookings_received,
        'total_revenue': total_revenue,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def profile_setup(request):
    if request.method == 'POST':
        user_type = request.POST['user_type']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        Profile.objects.create(
            user=request.user,
            user_type=user_type,
            phone_number=phone_number,
            address=address
        )
        return redirect('dashboard')
    return render(request, 'core/profile_setup.html', {})