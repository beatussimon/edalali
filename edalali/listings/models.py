from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Amenity(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # e.g., Font Awesome class

    def __str__(self):
        return self.name

class Location(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.address

class Listing(models.Model):
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    property_type = models.CharField(max_length=50)  # "House", "Apartment", etc.
    room_type = models.CharField(max_length=50)
    accommodates = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    beds = models.PositiveIntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1)])
    is_available = models.BooleanField(default=True)
    amenities = models.ManyToManyField(Amenity, blank=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')
    # caption = models.CharField(max_length=255, blank=True) # Optional

    def __str__(self):
        return f"Image for {self.listing.title}"