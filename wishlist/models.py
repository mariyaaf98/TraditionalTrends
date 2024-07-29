from django.db import models
from accounts.models import User
from product_management.models import Product_Variant

class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(Product_Variant, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        return f"{self.variant.product.product_name} - {self.variant.colour_name} in {self.user.username}'s wishlist"
