from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Book(models.Model):
    title = models.CharField(max_length=255, blank=False, null=True)
    author = models.CharField(max_length=255,blank=False, null=True)
    description = models.TextField(max_length=500)
    synopsis = models.TextField(max_length=500)
    genre = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=False, unique=True)
    address = models.TextField(blank=True)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  

    def __str__(self):
        return self.user.username

    def update_total_spent(self, amount):
        self.total_spent += amount
        self.save()


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f'Review by {self.user.username} for {self.book.title}'


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'book')

    def __str__(self):
        return f'{self.quantity} of {self.book.title} in cart of {self.customer.user.username}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f'Order {self.id} by {self.customer.user.username}'

    def calculate_total(self):
        total = sum(item.get_total_price() for item in self.items.all())
        total -= total * ( Decimal(self.discount) / Decimal(100)) 
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  

    def __str__(self):
        return f'{self.quantity} of {self.book.title} in order {self.order.id}'

    def get_total_price(self):
        return self.price * self.quantity * (1 - self.discount / 100)