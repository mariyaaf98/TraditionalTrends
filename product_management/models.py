from django.db import models
from category_management.models import Category
from brand_management.models import Brand
from accounts.models import User

class Products(models.Model):
    product_name = models.CharField(max_length=100, null=False)
    product_description = models.TextField(max_length=5000, null=False)
    product_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    product_brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.ImageField(upload_to="images/thumbnail_images", null=True)

    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def percentage_discount(self):
        return int(((self.price - self.offer_price) / self.price) * 100)

    def __str__(self):
        return f"{self.product_brand.brand_name}-{self.product_name}"


class Product_images(models.Model):
    product = models.ForeignKey(Products, related_name='product_images_set', on_delete=models.CASCADE)
    images = models.ImageField(upload_to="images/product_images", default="")

    def __str__(self):
        return f"Image for {self.product.product_name}"
    