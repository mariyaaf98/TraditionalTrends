from django.db import models
from django.utils import timezone
from accounts.models import User
from order_management.models import Order

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    is_percentage = models.BooleanField(default=False)
    expiration_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.is_active and self.expiration_date > timezone.now() 


class UserCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, null=True)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.coupon.code}"