from django.contrib import admin
from .models import Listing, Amenity, Location, ListingImage

class ListingImageInline(admin.TabularInline):  # Or StackedInline
    model = ListingImage
    extra = 1

class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = ('title', 'host', 'price_per_night', 'is_available')
    list_filter = ('is_available', 'property_type', 'room_type')
    search_fields = ('title', 'description', 'location__city')
    prepopulated_fields = {'slug': ('title',)}  # Automatically populate slug

admin.site.register(Listing, ListingAdmin)
admin.site.register(Amenity)
admin.site.register(Location)
admin.site.register(ListingImage)