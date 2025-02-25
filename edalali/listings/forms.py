from django import forms
from .models import Listing, ListingImage, Location


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = ['host', 'is_available', 'slug']

    # Separate Location fields for ease of input
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    country = forms.CharField(max_length=100)
    zip_code = forms.CharField(max_length=10)

    def save(self, commit=True):
        # 1. Get or Create the Location
        location, _ = Location.objects.get_or_create(
            address=self.cleaned_data['address'],
            city=self.cleaned_data['city'],
            state=self.cleaned_data['state'],
            country=self.cleaned_data['country'],
            zip_code=self.cleaned_data['zip_code'],
        )

        # 2. Create the Listing instance (but don't save to DB yet)
        instance = super().save(commit=False)
        instance.location = location  # Associate the Listing with the Location

        # 3. Save to the database (if commit=True)
        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many fields (amenities)

        return instance


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image']


ListingImageFormSet = forms.inlineformset_factory(
    Listing,  # Parent model
    ListingImage,  # Child model
    form=ListingImageForm,  # The form to use for each image
    extra=3,  # How many extra image forms to show initially
    can_delete=True,  # Allow deleting existing images
)