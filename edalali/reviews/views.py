from django.shortcuts import render, redirect, get_object_or_404
from .models import Review
from .forms import ReviewForm
from listings.models import Listing
from bookings.models import Booking #import booking
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

@login_required
def create_review(request, listing_slug):
    listing = get_object_or_404(Listing, slug=listing_slug)

    # Check if the user has a completed booking for this listing
    has_booking = Booking.objects.filter(
        user=request.user,
        listing=listing,
        is_confirmed=True,
        check_out_date__lt=timezone.now().date()  # Check-out date is in the past
    ).exists()

    if not has_booking:
        messages.error(request, "You can only leave a review after a completed booking.")
        return redirect('listing_detail', slug=listing_slug)

    # Check if the user has already reviewed this listing
    if Review.objects.filter(user=request.user, listing=listing).exists():
        messages.error(request,"You have already submitted a review for this listing")
        return redirect('listing_detail', slug=listing_slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.listing = listing
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('listing_detail', slug=listing_slug)
    else:
        form = ReviewForm()

    return render(request, 'reviews/create_review.html', {'form': form, 'listing': listing})