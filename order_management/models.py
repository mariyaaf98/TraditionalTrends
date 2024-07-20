from django.db import models
from django.utils import timezone
from accounts.models import User
from product_management.models import Product_Variant


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.FloatField(null=False)
    date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=100, default="Order Placed")
    payment_option = models.CharField(max_length=100, default="cash_on_delivery")
    order_id = models.CharField(max_length=100, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    payment_status = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.IntegerField(blank=True, null=True)

    # Address Fields
    name = models.CharField(max_length=50)
    house_name = models.CharField(max_length=400)
    street_name = models.CharField(max_length=300)
    pin_number = models.CharField(max_length=10)
    district = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        super(Order, self).save(*args, **kwargs)

    def generate_order_id(self):
        return f"ORDER-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.user.id}"

    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"




class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    main_order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(Product_Variant, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=False, default=1)
    is_active = models.BooleanField(default=True)

    def total_cost_coupon(self):
        unit_price = self.variant.product.offer_price * self.quantity
        if self.variant.product.product_category.discount:
            discount = self.variant.product.product_category.discount
            discount_amount = unit_price * (discount / 100)
            unit_price -= discount_amount
        return unit_price

    def total_cost(self):
        return self.quantity * self.variant.product.offer_price

    def __str__(self):
        return f"{self.quantity} of {self.variant.product.product_name} in order {self.main_order.order_id}"

    
   

