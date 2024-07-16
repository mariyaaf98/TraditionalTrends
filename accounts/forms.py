from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'id': 'join_confirm_password',
        'required': True
    }))

    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'phone', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Full Name',
                'id': 'join_full_name',
                'required': True
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'Username',
                'id': 'join_username',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address',
                'id': 'join_email_address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '123-456-7890',
                'id': 'phone',
                'required': True
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Password',
                'id': 'join_password',
                'required': True
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Password and Confirm Password do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        max_length=254,
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True, 'placeholder': 'Email'})
    )

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("This field is required.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError("This field is required.")
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError("This field is required.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("This field is required.")
        return phone