from django import forms
from .models import Coupon
from django.utils import timezone

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code',
            'discount',
            'is_percentage',
            'expiration_date',
            'is_active',
            'minimum_purchase_amount',
        ]
        widgets = {
            'expiration_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type here'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount amount'}),
            'is_percentage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum amount'}),
        }

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date < timezone.now():
            raise forms.ValidationError('Expiration date cannot be in the past.')
        return expiration_date

    def clean(self):
        cleaned_data = super().clean()
        is_percentage = cleaned_data.get('is_percentage')
        discount = cleaned_data.get('discount')

        # Validate discount based on percentage or fixed amount
        if is_percentage and (discount <= 0 or discount > 100):
            self.add_error('discount', 'Discount percentage must be between 1 and 100.')
        elif not is_percentage and discount <= 0:
            self.add_error('discount', 'Discount amount must be greater than 0.')

        return cleaned_data
