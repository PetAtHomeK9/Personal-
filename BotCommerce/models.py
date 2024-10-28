from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=100) #Telegram user ID
    status = models.CharField(max_length=50, default='PENDING') #PENDING, PAID, COMPLETED
    receipt_img = models.ImageField(upload_to='receipts/', null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} by User {self.user_id}"