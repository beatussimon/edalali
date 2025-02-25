from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
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