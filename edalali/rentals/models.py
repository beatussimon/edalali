from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    """Custom user manager for email as username."""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model using email as the unique identifier."""
    username = models.CharField(max_length=1, null=True, blank=True, unique=False)  # Optional: if you want a username
    email = models.EmailField(_('email address'), unique=True)  # Email will be the unique identifier

    USERNAME_FIELD = 'email'  # Use email as the login field
    REQUIRED_FIELDS = []  # Remove username from required fields

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse('profile')


class Profile(models.Model):
    """User profile with additional information."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.email



class Amenity(models.Model):
    """Amenities available for listings (e.g., WiFi, Parking, etc.)."""
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # e.g., Font Awesome class

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Amenities"


class Location(models.Model):
    """Represents the location of a listing."""
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
    """Represents a rental listing."""
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)  # For SEO-friendly URLs
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    property_type = models.CharField(max_length=50)
    room_type = models.CharField(max_length=50)
    accommodates = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    beds = models.PositiveIntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1)])
    amenities = models.ManyToManyField(Amenity, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
             self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def get_absolute_url(self):
        return reverse("listing_detail", kwargs={"slug": self.slug})

class ListingImage(models.Model):
    """Images associated with a listing."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return f"Image for {self.listing.title}"

class Booking(models.Model):
    """Represents a booking for a listing."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_guests = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

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
                is_confirmed=True
            ).exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError("This listing is already booked for the selected dates.")
    def calculate_total_price(self):
        if self.check_in_date and self.check_out_date and self.listing:
            num_nights = (self.check_out_date - self.check_in_date).days
            self.total_price = num_nights * self.listing.price_per_night
        else:
            self.total_price = None

    def save(self, *args, **kwargs):
        self.calculate_total_price()
        super().save(*args, **kwargs)
    def get_absolute_url(self):
        return reverse("booking_detail", kwargs={"pk": self.pk})


class Availability(models.Model):
    """Tracks availability of a listing on specific dates."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('listing', 'date')
        verbose_name_plural = "Availabilities"

    def __str__(self):
        return f"{self.listing.title} - {self.date}: {'Available' if self.is_available else 'Blocked'}"

class Review(models.Model):
    """Represents a user review for a listing."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('listing', 'user')

    def __str__(self):
        return f"Review for {self.listing.title} by {self.user.email}"
    def get_absolute_url(self):
        return reverse("listing_detail", kwargs={"slug": self.listing.slug})


class Conversation(models.Model):
    """Represents a conversation between users."""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation between {', '.join([str(p) for p in self.participants.all()])}"

class Message(models.Model):
    """Represents a message within a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation}"

    class Meta:
        ordering = ['created_at']

class Payment(models.Model):
    """Represents a payment for a booking (simplified for this example)."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=255, blank=True)  # From Stripe/payment processor
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # e.g., 'pending', 'success', 'failed'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for booking {self.booking.id}"