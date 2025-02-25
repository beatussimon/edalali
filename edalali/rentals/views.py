from django.shortcuts import render, get_object_or_404, redirect
from .models import Listing, Booking, Review, Conversation, Message, Payment, Availability
from .forms import ListingForm, ListingImageFormSet, BookingForm, ReviewForm, MessageForm,  ProfileUpdateForm, PaymentForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.conf import settings
import stripe
from django.db.models import Q, Count  # Import Q and Count


stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def profile(request):
    return render(request, 'rentals/profile.html')
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'rentals/edit_profile.html', {'form': form})


def home(request):
    """Displays the homepage with featured listings."""
    today = timezone.now().date()
    # Find listings that have *any* availability in the future
    featured_listings = Listing.objects.filter(
        availability__date__gte=today,
        availability__is_available=True
    ).distinct().order_by('-price_per_night')[:3]
    return render(request, 'rentals/home.html', {'featured_listings': featured_listings})



def listing_list(request):
    """Displays a list of available listings."""
    today = timezone.now().date()
    # Find listings that have *any* availability in the future.
    listings = Listing.objects.filter(
        availability__date__gte=today,
        availability__is_available=True
    ).distinct()  # Use distinct() to avoid duplicates

    return render(request, 'rentals/listing_list.html', {'listings': listings})



def listing_detail(request, slug):
    """Displays details for a single listing."""
    listing = get_object_or_404(Listing, slug=slug)
    today = timezone.now().date()
    return render(request, 'rentals/listing_detail.html', {'listing': listing, 'today': today})


@login_required
@transaction.atomic
def create_listing(request):
    """Handles the creation of a new listing."""
    if request.method == 'POST':
        form = ListingForm(request.POST)
        formset = ListingImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.host = request.user
            listing.save()  # Save to get a listing ID
            formset.instance = listing
            formset.save()

            # Create Availability records for the new listing (e.g., next 365 days)
            today = timezone.now().date()
            for i in range(365):
                Availability.objects.create(listing=listing, date=today + timezone.timedelta(days=i))

            messages.success(request, 'Listing created successfully!')
            return redirect('listing_detail', slug=listing.slug)
        else:
            messages.error(request,"Correct the errors below")
    else:
        form = ListingForm()
        formset = ListingImageFormSet()
    return render(request, 'rentals/listing_create_form.html', {'form': form, 'formset': formset})


@login_required
@transaction.atomic
def edit_listing(request, slug):
    """Handles editing an existing listing."""
    listing = get_object_or_404(Listing, slug=slug)

    if request.user != listing.host:
        return HttpResponseForbidden("You don't have permission to edit this listing.")

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Listing updated successfully")
            return redirect('listing_detail', slug=listing.slug)
        else:
            messages.error(request,"Correct the errors below")
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(instance=listing)

    return render(request, 'rentals/listing_edit_form.html', {'form': form, 'formset': formset, 'listing':listing})


@login_required
def create_booking(request, listing_slug):
    """Handles creating a new booking for a listing."""
    listing = get_object_or_404(Listing, slug=listing_slug)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.listing = listing
            booking.save()  # Save to generate ID for payment
            messages.success(request,"Booking request submitted")
            return redirect('create_payment', booking_id=booking.id) # Go to payment
        else:
            messages.error(request,"Correct the errors below")
    else:
        form = BookingForm()

    return render(request, 'rentals/booking_form.html', {'form': form, 'listing': listing})


@login_required
def my_bookings(request):
    """Displays a list of the user's bookings."""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    today = timezone.now().date()
    return render(request, 'rentals/my_bookings.html', {'bookings': bookings, 'today':today})


@login_required
def cancel_booking(request, booking_id):
    """Handles cancelling a booking."""
    booking = get_object_or_404(Booking, pk=booking_id)

    if booking.user != request.user:
        return HttpResponseForbidden("You are not allowed to cancel this booking.")

    if request.method == 'POST':
          # In a real app, you would handle refunds and credits here
        if booking.payment and booking.payment.status == 'success':
            # Handle refund with Stripe (IMPORTANT!)
            try:
                refund = stripe.Refund.create(
                    charge=booking.payment.transaction_id,
                )
                booking.payment.status = 'refunded'  # Update payment status
                booking.payment.save()
            except stripe.error.StripeError as e:
                messages.error(request, f"Refund failed: {e}")
                return redirect('my_bookings')
        booking.is_confirmed = False  # Or have a separate 'cancelled' status
        booking.save()
        messages.success(request,"Booking Canceled")
        return redirect('my_bookings')

    return render(request, 'rentals/booking_confirm.html', {'booking': booking, 'action': 'cancel'})

@login_required
@transaction.atomic
def create_review(request, slug):
    """Handles the creation of a new review for a listing."""
    listing = get_object_or_404(Listing, slug=slug)
    today = timezone.now().date()

    # Check if the user has a completed, confirmed booking for this listing
    has_valid_booking = Booking.objects.filter(
        user=request.user,
        listing=listing,
        is_confirmed=True,
        check_out_date__lt=today  # Check-out date is in the past
    ).exists()

    if not has_valid_booking:
        messages.error(request, "You can only review listings you have booked and stayed in.")
        return redirect('listing_detail', slug=listing.slug)  # Redirect back to the listing

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.listing = listing
            review.save()
            messages.success(request, 'RevieCCw submitted successfully!')
            return redirect('listing_detail', slug=listing.slug)
    else:
        form = ReviewForm()
    return render(request, 'rentals/review_form.html', {'form': form, 'listing': listing})
@login_required
def inbox(request):
    """Displays a list of the user's conversations."""
    conversations = request.user.conversations.all()
    return render(request, 'rentals/inbox.html', {'conversations': conversations})

@login_required
def conversation_detail(request, conversation_id):
    """Displays the messages within a conversation and allows sending new messages."""
    conversation = get_object_or_404(Conversation, pk=conversation_id)

    if request.user not in conversation.participants.all():
       return HttpResponseForbidden("You are not part of this conversation")

    messages_list = conversation.messages.all()
    #Mark messages sent by other users as read
    unread_messages = messages_list.filter(is_read = False).exclude(sender=request.user)
    for message in unread_messages:
        message.is_read = True
        message.save()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    return render(request, 'rentals/message_form.html', {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
    })

@login_required
def start_conversation(request, user_id):
    """Starts a new conversation with another user (if one doesn't exist)."""
    recipient = get_object_or_404(settings.AUTH_USER_MODEL, pk=user_id)

    # Check for existing conversation
    existing_conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient)
    if existing_conversation.exists():
        return redirect('conversation_detail', conversation_id=existing_conversation.first().id)

    # Create a new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, recipient)
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def my_listings(request):
    """Displays a list of listings created by the current user."""
    listings = Listing.objects.filter(host=request.user)
    return render(request, 'rentals/my_listings.html', {'listings': listings})

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    #Authorization check
    if request.user != booking.user and request.user != booking.listing.host:
        return HttpResponseForbidden("You don't have permission to view this booking")
    return render(request, 'rentals/booking_detail.html', {'booking': booking})

@login_required
@transaction.atomic
def create_payment(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    if request.user != booking.user:
         return HttpResponseForbidden("You don't have permission to view this booking")

    if booking.payment:
        messages.error(request,'Payment already created')
        return redirect('booking_detail', booking_id=booking.id)


    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # 1. Process Payment with Stripe (Simplified - See Notes Below)
            try:
                charge = stripe.Charge.create(
                    amount=int(booking.total_price * 100),  # Amount in cents
                    currency='usd',  # Change as needed
                    description=f'Booking {booking.id} for {booking.listing.title}',
                    source=form.cleaned_data['stripe_token'],  # Get the token from the form
                )
                # 2. Create Payment Object
                payment = Payment.objects.create(
                    booking=booking,
                    transaction_id=charge.id,  # Store Stripe's charge ID
                    amount=booking.total_price,
                    status='success'  # Or 'pending' if using asynchronous methods
                )
                booking.is_confirmed = True
                booking.save()

                messages.success(request,"Payment Successfull")
                return redirect('payment_success', booking_id=booking.id)

            except stripe.error.StripeError as e:
                # Handle Stripe errors (card declined, etc.)
                messages.error(request, str(e))
                return render(request, 'rentals/payment_form.html', {'form': form, 'booking': booking, 'stripe_public_key': settings.STRIPE_PUBLIC_KEY})
    else:
        form = PaymentForm()

    return render(request, 'rentals/payment_form.html', {'form': form, 'booking': booking,  'stripe_public_key': settings.STRIPE_PUBLIC_KEY})

@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking,pk=booking_id)
    if request.user != booking.user:
        return HttpResponseForbidden("You don't have permission to view this booking")
    return render(request, 'rentals/payment_success.html', {'booking': booking})

@login_required
def payment_cancel(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.user:
        return HttpResponseForbidden("You don't have permission to view this booking")
    return render(request, 'rentals/payment_cancel.html', {'booking': booking})