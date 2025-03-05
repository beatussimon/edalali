from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Listing(models.Model):
    RENTAL_TYPES = (
        ('property', 'Property'),
        ('equipment', 'Equipment'),
        ('service', 'Service'),
        ('package', 'Package'),
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    is_available = models.BooleanField(default=True)
    instant_book = models.BooleanField(default=False)
    images = models.ManyToManyField('ListingImage', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    image = models.ImageField(upload_to='listings/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Availability(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='availability')
    start_date = models.DateField()
    end_date = models.DateField()

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    USER_TYPES = (
        ('individual', 'Individual'),
        ('business', 'Business'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='individual')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)