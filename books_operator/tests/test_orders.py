from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from books_operator.models import User, Customer, Order, OrderItem, Cart, Book

class OrderViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='testpassword')
        self.admin_user = User.objects.create_user(username='admin', password='testpassword', is_staff=True)
        self.customer = Customer.objects.create(user=self.user, phone_number='1234567890')
        self.admin_customer = Customer.objects.create(user=self.admin_user, phone_number='1234567891')

        self.book = Book.objects.create(title='Sample Book', price=10.00)
        self.cart_item = Cart.objects.create(customer=self.customer, book=self.book, quantity=1)

        # Создаем заказ для теста
        self.order = Order.objects.create(customer=self.customer, discount=0.00)
        OrderItem.objects.create(order=self.order, book=self.book, quantity=1, price=self.book.price)
        

        # URL для API
        self.order_url = reverse('orders-list') 
        self.create_url = reverse('orders-create-order')  
        self.order_detail_url = reverse('orders-detail', kwargs={'pk': self.order.id})

        self.user_token = str(AccessToken.for_user(self.user))
        self.admin_token = str(AccessToken.for_user(self.admin_user))

        self.client = APIClient()

    def api_authentication(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_user_can_view_their_orders(self):
        self.api_authentication(self.user_token)

        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)   
        self.assertEqual(response.data[0]['id'], self.order.id)   

    def test_admin_can_view_all_orders(self):
        self.api_authentication(self.admin_token)

        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)   
        self.assertEqual(response.data[0]['id'], self.order.id)   

    def test_user_can_create_order_from_cart(self):
        self.api_authentication(self.user_token)

        response = self.client.post(self.create_url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.last()  
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.items.count(), 1)  
        self.assertEqual(order.items.first().book, self.book)   

    def test_user_cannot_create_order_from_empty_cart(self):
        self.cart_item.delete()   

        self.api_authentication(self.user_token)

        response = self.client.post(self.create_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Your cart is empty.")  

    def test_user_can_view_their_order(self):
        self.api_authentication(self.user_token)

        response = self.client.get(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)

    def test_admin_can_update_order_status(self):
        self.api_authentication(self.admin_token)

        response = self.client.patch(self.order_detail_url, {'status': 'processed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()  
        self.assertEqual(self.order.status, 'processed')

    def test_user_cannot_update_order_status(self):
        self.api_authentication(self.user_token)

        response = self.client.patch(self.order_detail_url, {'status': 'processed'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_filter_orders_by_customer_and_status(self):
        self.api_authentication(self.admin_token)

        order1 = Order.objects.create(customer=self.customer, status='pending')
        order2 = Order.objects.create(customer=self.customer, status='shipped')
        order3 = Order.objects.create(customer=self.admin_customer, status='pending')
        order4 = Order.objects.create(customer=self.admin_customer, status='canceled')

        # Filter orders by customer ID for admin
        response = self.client.get(f"{self.order_url}?customer_id={self.customer.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) 

        # Filters orders by status for admin
        response = self.client.get(f"{self.order_url}?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  

        # Filters orders by customer ID and status 
        response = self.client.get(f"{self.order_url}?customer_id={self.customer.id}&status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Filter orders by status for user
        self.api_authentication(self.user_token)

        response = self.client.get(f"{self.order_url}?status=shipped")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for order in response.data:
            self.assertEqual(order['customer'], self.customer.id) 
