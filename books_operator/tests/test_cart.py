from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from books_operator.models import User, Cart, Customer, Book

class CartTestCase(APITestCase):
    def setUp(self):
        Customer.objects.all().delete()

        self.user = User.objects.create_user(username="user", password="password")
        self.admin_user = User.objects.create_user(username="admin", password="admin_password", is_staff=True)
        
        self.customer = Customer.objects.create(user=self.user, phone_number="1234567890")
        self.admin_customer = Customer.objects.create(user=self.admin_user, phone_number="1234567891")
        
        self.book1 = Book.objects.create(title="Book 1", price=100, discount=10)
        self.book2 = Book.objects.create(title="Book 2", price=200, discount=20)
        
        # Токены для аутентификации
        self.user_token = str(AccessToken.for_user(self.user))
        self.admin_token = str(AccessToken.for_user(self.admin_user))

        self.cart_item = Cart.objects.create(customer=self.customer, book=self.book1, quantity=1)
        self.cart_url = reverse('cart-detail', args=[self.cart_item.id])
        
        self.client = APIClient()

    def api_authentication(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_get_user_cart(self):
        self.api_authentication(self.user_token)

        Cart.objects.create(customer=self.customer, book=self.book2, quantity=2)

        response = self.client.get(reverse("cart-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        cart_item1 = response.data[0]
        cart_item2 = response.data[1]
        self.assertEqual(cart_item1["book_title"], "Book 1")
        self.assertEqual(cart_item1["quantity"], 1)
        self.assertEqual(cart_item2["book_title"], "Book 2")
        self.assertEqual(cart_item2["quantity"], 2)    

    def test_add_book_to_cart(self):
        self.api_authentication(self.user_token)
        
        # Try to add book
        response = self.client.post(reverse("cart-list"), {"book_id": self.book2.id, "quantity": 1})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to add same book againg to see quantity change
        response = self.client.post(reverse("cart-list"), {"book_id": self.book1.id, "quantity": 1})
        cart_item = Cart.objects.get(customer=self.customer, book=self.book1)
        self.assertEqual(cart_item.quantity, 2)
        
    def test_remove_book_from_cart(self):
        self.api_authentication(self.user_token)
        
        response = self.client.delete(reverse("cart-detail", args=[self.cart_item.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cart.objects.filter(customer=self.customer, book=self.book1).exists())

    def test_clear_cart(self):
        self.api_authentication(self.user_token)
        
        Cart.objects.create(customer=self.customer, book=self.book2, quantity=1)
        
        response = self.client.delete(reverse("cart-clear-cart"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  
        self.assertFalse(Cart.objects.filter(customer=self.customer).exists())

    def test_admin_can_view_specific_user_cart(self):
        self.api_authentication(self.admin_token)
        
        response = self.client.get(reverse("cart-user-cart", kwargs={"user_id": self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data[0]["book_title"], "Book 1")

    def test_discount_and_price_update_on_cart_view(self):
        self.api_authentication(self.user_token)
        
        self.book1.discount = 15.00
        self.book1.save()
        
        response = self.client.get(reverse("cart-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cart_item_data = response.data[0]
        self.assertEqual(cart_item_data["discount"], self.book1.discount)
        self.assertEqual(cart_item_data["book_price"], self.book1.price)

    def test_update_quantity_to_arbitrary_value(self):
        self.api_authentication(self.user_token)
        
        response = self.client.patch(self.cart_url, data={"quantity": 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 5) 
