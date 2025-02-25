from django.core.management.base import BaseCommand
from rentals.models import Listing, Location, Amenity, CustomUser
from faker import Faker
import random
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Creates 50 sample listings with locations and amenities.'

    def handle(self, *args, **options):
        fake = Faker()

        # --- Create Amenities (if they don't exist) ---
        amenities = [
            "WiFi", "Kitchen", "Heating", "Air conditioning", "Washer",
            "Dryer", "Free parking on premises", "TV", "Dedicated workspace",
            "Hair dryer", "Iron", "Smoke alarm", "Carbon monoxide alarm",
            "First aid kit", "Fire extinguisher", "Essentials", "Shampoo",
            "Hangers", "Bed linens", "Extra pillows and blankets", "Hot water",
            "Refrigerator", "Microwave", "Coffee maker", "Cooking basics",
            "Dishes and silverware", "Dishwasher", "Oven", "Stove",
            "Private entrance", "Patio or balcony", "Garden or backyard",
            "Luggage dropoff allowed", "Long term stays allowed",
            "Self check-in", "Keypad", "Smart lock", "Building staff",
            "Pets allowed", "Smoking allowed", "Events allowed",
            "Beachfront", "Waterfront", "Ski-in/Ski-out",
            "Lake access", "Pool", "Hot tub", "Gym", "Breakfast"
        ]
        for amenity_name in amenities:
            amenity, created = Amenity.objects.get_or_create(name=amenity_name) #Avoid duplicates
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created amenity: {amenity_name}'))

        # --- Get or create a host user ---
        #   (Replace with an existing user if you have one)
        try:
            host_user = CustomUser.objects.get(email='host@example.com')
            self.stdout.write(self.style.WARNING('Using existing user: host@example.com'))
        except CustomUser.DoesNotExist:
            host_user = CustomUser.objects.create_user(
                email='host@example.com',
                password='testpassword'  # Use a strong password!
            )
            host_user.first_name = "Test"
            host_user.last_name = "Host"
            host_user.is_staff = True #Give admin permissions
            host_user.save()
            self.stdout.write(self.style.SUCCESS('Created host user: host@example.com'))

         # Check for at least 5 amenities.  Important for the loop later.
        if Amenity.objects.count() < 5:
            self.stdout.write(self.style.ERROR('You need at least 5 amenities. Please add more.'))
            return


        # --- Create Listings ---
        for i in range(50):
            title = fake.sentence(nb_words=4)
            description = fake.paragraph(nb_sentences=5)

            # Create Location
            location = Location.objects.create(
                address=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                country=fake.country(),
                zip_code=fake.postcode(),
                latitude=float(fake.latitude()),  # Convert Decimal to float
                longitude=float(fake.longitude()), # Convert Decimal to float
            )

            # Create Listing
            listing = Listing.objects.create(
                host=host_user,
                title=title,
                description=description,
                location=location,
                property_type=random.choice(["House", "Apartment", "Condo", "Townhouse", "Villa"]),
                room_type=random.choice(["Entire place", "Private room", "Shared room"]),
                accommodates=random.randint(1, 10),
                bedrooms=random.randint(1, 5),
                beds=random.randint(1, 5),
                bathrooms=random.choice([1, 1.5, 2, 2.5, 3]),
                price_per_night=random.randint(50, 500),
            )

            # Add some random amenities (at least 3, up to 5)
            num_amenities = random.randint(3, 5)
            amenities_to_add = random.sample(list(Amenity.objects.all()), num_amenities)
            for amenity in amenities_to_add:
              listing.amenities.add(amenity)

            self.stdout.write(self.style.SUCCESS(f'Created listing: {title}'))

        self.stdout.write(self.style.SUCCESS('Successfully created 50 listings.'))