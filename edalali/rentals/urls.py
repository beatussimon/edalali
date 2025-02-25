from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('listings/', views.listing_list, name='listing_list'),
    path('listings/<slug:slug>/', views.listing_detail, name='listing_detail'),
    path('listings/create/', views.create_listing, name='create_listing'),
    path('listings/<slug:slug>/edit/', views.edit_listing, name='edit_listing'),
    path('listings/<slug:listing_slug>/book/', views.create_booking, name='create_booking'),
    path('bookings/my_bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('listings/<slug:listing_slug>/review/', views.create_review, name='create_review'),
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('new_conversation/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my_listings/', views.my_listings, name='my_listings'), # Host can view
    path('bookings/<int:booking_id>/payment/', views.create_payment, name='create_payment'),
    path('payment/success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('payment/cancel/<int:booking_id>/', views.payment_cancel, name='payment_cancel'),
]