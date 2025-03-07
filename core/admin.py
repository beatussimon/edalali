from django.contrib import admin
from .models import Category, Listing, ListingImage, Availability, Booking, Profile, Review, Message

admin.site.register(Category)
admin.site.register(Listing)
admin.site.register(ListingImage)
admin.site.register(Availability)
admin.site.register(Booking)
admin.site.register(Profile)
admin.site.register(Review)
admin.site.register(Message)