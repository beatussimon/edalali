from django import forms
from .models import Listing, ListingImage, Booking, Review, Message, Location, Profile # Import Profile
from django.forms import inlineformset_factory
from allauth.account.forms import SignupForm


class ListingForm(forms.ModelForm):
    """Form for creating and updating listings."""
    class Meta:
        model = Listing
        exclude = ['host', 'slug', 'is_available'] #is_available will be managed in the view
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    #Separate Location fields for ease of input
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
    """Form for uploading listing images."""
    class Meta:
        model = ListingImage
        fields = ['image']

ListingImageFormSet = inlineformset_factory(
    Listing, ListingImage, form=ListingImageForm,
    extra=3, can_delete=True
)

class BookingForm(forms.ModelForm):
    """Form for creating bookings."""
    class Meta:
        model = Booking
        fields = ['check_in_date', 'check_out_date', 'num_guests']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        listing = self.instance.listing # Access the listing from the instance

        if check_in and check_out and listing:
            #Check if check_out is after check_in:
            if check_out <= check_in:
                self.add_error('check_out_date', "Check-out date must be after check-in date.")
            # Check for overlapping bookings:
            overlapping_bookings = Booking.objects.filter(
                listing=listing,
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
                is_confirmed = True,
            ).exclude(pk=self.instance.pk if self.instance else None) # Exclude if updating
            if overlapping_bookings.exists():
                self.add_error('check_in_date', "This listing is already booked for the selected dates.")
        return cleaned_data

class ReviewForm(forms.ModelForm):
    """Form for submitting reviews."""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class MessageForm(forms.ModelForm):
    """Form for sending messages."""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message...'}),
        }

class PaymentForm(forms.Form):
    """
    Simplified payment form for demonstration.  In a real application, you would
    *not* collect sensitive card details directly.  Instead, you would use
    JavaScript libraries provided by your payment gateway (e.g., Stripe Elements)
    to securely tokenize the card information.
    """
    # These fields are for demonstration ONLY.  Do NOT use in production.
    card_number = forms.CharField(label='Card Number', max_length=19, required=False, widget=forms.TextInput(attrs={'placeholder': 'XXXX XXXX XXXX XXXX'})) #Added Widget
    expiry_date = forms.CharField(label='Expiry Date', max_length=7, required=False, widget=forms.TextInput(attrs={'placeholder': 'MM/YYYY'})) #Added Widget
    cvv = forms.CharField(label='CVV', max_length=4, required=False, widget=forms.TextInput(attrs={'placeholder': 'XXX'}))#Added Widget

    # Stripe Token (This is the critical field - will be populated by JavaScript)
    stripe_token = forms.CharField(widget=forms.HiddenInput, required=False) #This will be hidden

    def clean(self):
        """
        In a real application, this is where you would validate the *token*,
        not the raw card details.
        """
        cleaned_data = super().clean()
        if not cleaned_data.get('stripe_token'):
            self.add_error(None, "Payment processing failed. Please try again.") #General Error

        # We *never* handle raw card details in our backend.
        return cleaned_data

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'phone_number']


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, label='Last Name', widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


class ListingForm(forms.ModelForm):
    """Form for creating and updating listings."""
    class Meta:
        model = Listing
        exclude = ['host', 'slug', 'is_available'] #is_available will be managed in the view
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    #Separate Location fields for ease of input
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
    """Form for uploading listing images."""
    class Meta:
        model = ListingImage
        fields = ['image']

ListingImageFormSet = inlineformset_factory(
    Listing, ListingImage, form=ListingImageForm,
    extra=3, can_delete=True
)

class BookingForm(forms.ModelForm):
    """Form for creating bookings."""
    class Meta:
        model = Booking
        fields = ['check_in_date', 'check_out_date', 'num_guests']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        listing = self.instance.listing # Access the listing from the instance

        if check_in and check_out and listing:
            #Check if check_out is after check_in:
            if check_out <= check_in:
                self.add_error('check_out_date', "Check-out date must be after check-in date.")
            # Check for overlapping bookings:
            overlapping_bookings = Booking.objects.filter(
                listing=listing,
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
                is_confirmed = True,
            ).exclude(pk=self.instance.pk if self.instance else None) # Exclude if updating
            if overlapping_bookings.exists():
                self.add_error('check_in_date', "This listing is already booked for the selected dates.")
        return cleaned_data

class ReviewForm(forms.ModelForm):
    """Form for submitting reviews."""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class MessageForm(forms.ModelForm):
    """Form for sending messages."""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message...'}),
        }

class PaymentForm(forms.Form):
    """
    Simplified payment form for demonstration.  In a real application, you would
    *not* collect sensitive card details directly.  Instead, you would use
    JavaScript libraries provided by your payment gateway (e.g., Stripe Elements)
    to securely tokenize the card information.
    """
    # These fields are for demonstration ONLY.  Do NOT use in production.
    card_number = forms.CharField(label='Card Number', max_length=19, required=False, widget=forms.TextInput(attrs={'placeholder': 'XXXX XXXX XXXX XXXX'})) #Added Widget
    expiry_date = forms.CharField(label='Expiry Date', max_length=7, required=False, widget=forms.TextInput(attrs={'placeholder': 'MM/YYYY'})) #Added Widget
    cvv = forms.CharField(label='CVV', max_length=4, required=False, widget=forms.TextInput(attrs={'placeholder': 'XXX'}))#Added Widget

    # Stripe Token (This is the critical field - will be populated by JavaScript)
    stripe_token = forms.CharField(widget=forms.HiddenInput, required=False) #This will be hidden

    def clean(self):
        """
        In a real application, this is where you would validate the *token*,
        not the raw card details.
        """
        cleaned_data = super().clean()
        if not cleaned_data.get('stripe_token'):
            self.add_error(None, "Payment processing failed. Please try again.") #General Error

        # We *never* handle raw card details in our backend.
        return cleaned_data

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'phone_number']