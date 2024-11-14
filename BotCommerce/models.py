from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(Category, max_length=255)
    category_id = models.CharField(max_length=255, default='')
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ProductDetail(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    email = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Details for {self.product.name}"

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PENDING_RECEIPT', 'Pending Receipt'),
        ('COMPLETED', 'Completed'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=100)  # Product user ID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    receipt_img = models.ImageField(upload_to='receipts/', null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} by User {self.user_id}"

    # Method to get product details after purchase
    def get_product_details(self):
        try:
            # Accessing the ProductDetail associated with this product
            product_detail = ProductDetail.objects.get(product=self.product)
            details = {
                "email": product_detail.email,
                "password": product_detail.password,
            }
            return details
        except ProductDetail.DoesNotExist:
            return None  # Handle case if no details are found