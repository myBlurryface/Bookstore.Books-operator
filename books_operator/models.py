from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    title = models.CharField(max_length=255, blank=False, null=True)
    author = models.CharField(max_length=255,blank=False, null=True)
    description = models.TextField(max_length=500)
    synopsis = models.TextField(max_length=500)
    genre = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.title


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=False)
    address = models.TextField(blank=True)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  

    def __str__(self):
        return self.user.username

    def update_total_spent(self, amount):
        """Обновляет общее количество потраченных денег пользователем."""
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
        # Уникальность комбинации пользователь + книга
        unique_together = ('user', 'book')

    def __str__(self):
        return f'Review by {self.user.username} for {self.book.title}'


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.quantity} of {self.book.title} in cart of {self.customer.user.username}'

    def save(self, *args, **kwargs):
        """При сохранении корзины обновляем скидку из книги."""
        self.discount = self.book.discount
        super().save(*args, **kwargs)


class Order(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=255)  # Дублируем имя пользователя
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        """При сохранении заказа пересчитываем общую сумму."""
        self.total_price = sum(item.total_price for item in self.items.all())
        super().save(*args, **kwargs)

        # Обновляем сумму потраченных денег у пользователя
        if self.customer:
            self.customer.update_total_spent(self.total_price)

    def __str__(self):
        return f'Order #{self.id} by {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True, blank=True)
    book_title = models.CharField(max_length=255)  # Дублируем название книги
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Сохранение скидки
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """Заполняем данные о книге при сохранении и пересчитываем общую стоимость."""
        # Заполняем название книги, цену и скидку при создании позиции
        if self.book:
            self.book_title = self.book.title  # Сохраняем название книги
            self.price_per_item = self.book.price  # Сохраняем цену за единицу
            self.discount = self.book.discount  # Сохраняем скидку на момент покупки

        # Рассчитываем общую стоимость для позиции
        self.total_price = (self.price_per_item * (1 - self.discount / 100)) * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity} x {self.book_title} for Order #{self.order.id}'
