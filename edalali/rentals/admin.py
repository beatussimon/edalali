from django.contrib import admin
from .models import (CustomUser, Profile, Listing, ListingImage,
                     Amenity, Location, Booking, Review, Conversation, Message, Payment, Availability)  # Import Availability
from django.utils import timezone
from django.db.models import Exists, OuterRef

# Customizing the User Admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)

# Inlines
class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1

class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = ('title', 'host', 'price_per_night', 'is_currently_available')  # Changed method name
    list_filter = ('property_type', 'room_type', 'location__city') # removed is_available
    search_fields = ('title', 'description', 'location__city')
    prepopulated_fields = {'slug': ('title',)}

    def get_queryset(self, request):
        """
        Efficiently annotate the queryset with availability information.
        """
        today = timezone.now().date()
        # Check for *any* availability record for today
        availability_subquery = Availability.objects.filter(
            listing=OuterRef('pk'),
            date=today,
            is_available=True  # Check if it's available *today*
        )
        queryset = super().get_queryset(request).annotate(
            currently_available=Exists(availability_subquery)
        )
        return queryset


    def is_currently_available(self, obj):
        return obj.currently_available  # Use the annotated field

    is_currently_available.boolean = True
    is_currently_available.short_description = 'Available Today'  # Better description
    is_currently_available.admin_order_field = 'currently_available' #Allow sorting


class BookingAdmin(admin.ModelAdmin):
    list_display = ('listing', 'user', 'check_in_date', 'check_out_date', 'is_confirmed')
    list_filter = ('is_confirmed', 'listing', 'user')
    search_fields = ('listing__title', 'user__email')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('listing', 'user', 'rating', 'created_at')
    list_filter = ('listing', 'user', 'rating')
    search_fields = ('listing__title', 'user__email', 'comment')

class ConversationAdmin(admin.ModelAdmin):
     list_display = ('id','created_at', 'updated_at')  # Customize as needed
     search_fields = ('participants__email',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content', 'created_at', 'is_read')
    list_filter = ('conversation', 'sender', 'is_read')
    search_fields = ('conversation__participants__email', 'sender__email', 'content')


# Register your models here.
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Amenity)
admin.site.register(Location)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Payment)
admin.site.register(Availability) # Register availability