from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from listings.models import Listing  # Import Listing
from django.utils import timezone

class Booking(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_guests = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) #for record purpose

    def __str__(self):
        return f"Booking for {self.listing.title} by {self.user.email}"

    def clean(self):
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError("Check-out date must be after check-in date.")

            overlapping_bookings = Booking.objects.filter(
                listing=self.listing,
                check_in_date__lt=self.check_out_date,
                check_out_date__gt=self.check_in_date,
                is_confirmed = True,
            ).exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError("This listing is already booked for the selected dates.")

    def calculate_total_price(self):
        if self.check_in_date and self.check_out_date and self.listing:
            num_nights = (self.check_out_date - self.check_in_date).days
            self.total_price = num_nights * self.listing.price_per_night
        else :
            self.total_price = None

    def save(self, *args, **kwargs):
        self.calculate_total_price()
        super().save(*args, **kwargs)

class Availability(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('listing', 'date')
        verbose_name_plural = "Availabilities"

    def __str__(self):
        return f"{self.listing.title} - {self.date}: {'Available' if self.is_available else 'Blocked'}"