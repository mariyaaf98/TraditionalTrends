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
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount amount', 'step': '0.01'}),
            'is_percentage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum amount', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_percentage = cleaned_data.get('is_percentage')
        discount = cleaned_data.get('discount')

        if discount is not None:
            if discount <= 0:
                self.add_error('discount', 'Discount must be greater than 0.')
            elif is_percentage and discount > 65:
                self.add_error('discount', 'Discount percentage cannot be greater than 65.')
            elif not is_percentage and discount > 9999999.99:  # Max allowed by DecimalField(max_digits=8, decimal_places=2)
                self.add_error('discount', 'Discount amount cannot be greater than 9,999,999.99.')
        else:
            self.add_error('discount', 'Discount is required.')

        return cleaned_data