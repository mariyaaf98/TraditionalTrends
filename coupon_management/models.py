from django.db import models
from django.utils import timezone
from accounts.models import User

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    is_percentage = models.BooleanField(default=False)
    expiration_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.is_active and self.expiration_date > timezone.now() and (self.usage_limit is None or self.times_used < self.usage_limit)
