from django.shortcuts import render, redirect, get_object_or_404
from .models import Booking
from .forms import BookingForm
from listings.models import Listing
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden

@login_required
def create_booking(request, listing_slug):
    listing = get_object_or_404(Listing, slug=listing_slug)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.listing = listing
            booking.save() # This also calls calculate_total_price
            messages.success(request, 'Booking request submitted successfully!')
            return redirect('listing_detail', slug=listing_slug)  # Redirect to listing detail
        else:
             messages.error(request, "Correct the errors below")
    else:
        form = BookingForm()

    return render(request, 'bookings/create_booking.html', {'form': form, 'listing': listing})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')  # Show recent first
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    # Check if the user owns this booking
    if booking.user != request.user:
        return HttpResponseForbidden("You are not allowed to cancel this booking.")

    if request.method == 'POST':
          # In a real app, you would likely handle refunds/credits here
          booking.is_confirmed = False
          booking.save()
          messages.success(request, "Your Booking has been cancelled")
          return redirect('my_bookings') # Redirect to my bookings

    return render(request, 'bookings/cancel_booking.html', {'booking':booking})