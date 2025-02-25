from django.shortcuts import render, get_object_or_404, redirect
from .models import Listing
from .forms import ListingForm, ListingImageFormSet
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone 

def listing_list(request):
    listings = Listing.objects.filter(is_available=True)  # Show only available listings
    return render(request, 'listings/listing_list.html', {'listings': listings})

def listing_detail(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    today = timezone.now().date()  # Get today's date
    return render(request, 'listings/listing_detail.html', {'listing': listing, 'today': today})


@login_required
@transaction.atomic # Wrap in a transaction for data consistency
def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        formset = ListingImageFormSet(request.POST, request.FILES) #For multiple images
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.host = request.user
            listing.save() # Save listing first to generate PK
            formset.instance = listing  # Associate images with the listing
            formset.save()
            messages.success(request, 'Listing created successfully!')
            return redirect('listing_detail', slug=listing.slug)  # Redirect to listing detail
        else:
            messages.error(request, "Correct the errors below")
    else:
        form = ListingForm()
        formset = ListingImageFormSet()
    return render(request, 'listings/create_listing.html', {'form': form, 'formset': formset})

@login_required
@transaction.atomic
def edit_listing(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    # Authorization check: Ensure the user editing is the host
    if request.user != listing.host:
        messages.error(request, "You don't have permission to edit this listing.")
        return redirect('listing_detail', slug=listing.slug)

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Listing updated successfully")
            return redirect('listing_detail', slug=listing.slug)
        else:
            messages.error(request, "Correct the errors below")
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(instance=listing)  # Pass the listing instance
    return render(request, 'listings/edit_listing.html', {'form': form, 'formset': formset, 'listing':listing})