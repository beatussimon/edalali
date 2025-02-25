from django.urls import path
from . import views

urlpatterns = [
   path('listing/<slug:listing_slug>/book/', views.create_booking, name='create_booking'),
   path('my_bookings/', views.my_bookings, name='my_bookings'), # View user's bookings
   path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'), # Cancel
   # Add more URLs as needed (e.g., for viewing booking details, confirming bookings)
]