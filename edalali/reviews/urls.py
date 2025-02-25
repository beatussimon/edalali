from django.urls import path
from . import views

urlpatterns = [
    path('listing/<slug:listing_slug>/review/', views.create_review, name='create_review'),
    # Add other URLs as needed (e.g., for editing/deleting reviews)
]