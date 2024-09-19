from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    category_name = models.CharField(max_length=40, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    minimum_amount = models.CharField(max_length=40, null=True)
    discount = models.IntegerField(null=True)
    expirydate = models.DateField(null=True)
    is_deleted = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.category_name