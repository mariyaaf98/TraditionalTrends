from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models



class UserManager(BaseUserManager):
    def create_user(self, email, username, full_name, phone, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        if not full_name:
            raise ValueError("Users must have a full name")
        if not phone:
            raise ValueError("Users must have a phone number")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            full_name=full_name,
            phone=phone,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, full_name, phone, password):
        user = self.create_user(
            email=email,
            username=username,
            full_name=full_name,
            phone=phone,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    username = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, null=True, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'phone']

    def _str_(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    class Meta:
        ordering = ('email',)