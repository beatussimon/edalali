from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('listings/', views.listing_list, name='listing_list'),
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('create-listing/', views.create_listing, name='create_listing'),
    path('book/<int:pk>/', views.book_listing, name='book_listing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
]