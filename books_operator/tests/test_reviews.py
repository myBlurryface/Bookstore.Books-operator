from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from books_operator.models import User, Customer


class CustomerViewSetTest(APITestCase):
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        self.admin_customer = Customer.objects.create(
            user=self.admin_user,
            phone_number='1111111111'
        )

        # Создаем обычного пользователя
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='userpass'
        )

        self.regular_customer = Customer.objects.create(
            user=self.regular_user,
            phone_number='1234567890'
        )

        # Создаем еще одного обычного пользователя
        self.another_user = User.objects.create_user(
            username='another_user',
            email='another@test.com',
            password='anotherpass'
        )
        self.another_customer = Customer.objects.create(
            user=self.another_user,
            phone_number='9876543210'
        )

        self.regular_token = str(AccessToken.for_user(self.regular_user))
        self.admin_token = str(AccessToken.for_user(self.admin_user))

        self.profile_url = reverse('customer-profile')

        self.client = APIClient()
    
    def api_authentication(self, token):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_jwt_authentication(self):
        url = reverse('token_obtain_pair')

        response = self.client.post(url, {'username': 'user', 'password': 'userpass'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.api_authentication(self.regular_token)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile_as_regular_user(self):
        self.api_authentication(self.regular_token)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)
        self.assertEqual(response.data['phone_number'], self.regular_customer.phone_number)

    def test_get_profile_as_admin(self):
        self.api_authentication(self.admin_token)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Customer.objects.count())

    def test_update_profile_as_regular_user(self):
        self.api_authentication(self.regular_token)
        url = reverse('customer-detail', args=[self.regular_customer.id])
        data = {'phone_number': '9876543211'}
    
        response = self.client.patch(url, data, format='json')
        self.regular_customer.refresh_from_db()
        self.assertEqual(self.regular_customer.phone_number, '9876543211')

    def test_update_another_profile_as_admin(self):
        self.api_authentication(self.admin_token)

        url = reverse('customer-detail', args=[self.regular_customer.id])
        data = {'phone_number': '9876543211',}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_customer.refresh_from_db()
        self.assertEqual(self.regular_customer.phone_number, '9876543211')

    def test_create_customer_while_logged_in(self):
        self.api_authentication(self.regular_token)

        url = reverse('customer-list')
        data = {'username': 'new_user','phone_number': '0987654321',}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_profile_as_regular_user(self):
       self.api_authentication(self.regular_token)

       url = reverse('customer-detail', args=[self.regular_customer.id])

       response = self.client.delete(url)
       self.assertEqual(response.status_code, status.HTTP_200_OK)
       self.assertFalse(Customer.objects.filter(id=self.regular_customer.id).exists())
       self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())  
    def test_delete_profile_as_admin(self):
        self.api_authentication(self.admin_token)

        url = reverse('customer-detail', args=[self.regular_customer.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Customer.objects.filter(id=self.regular_customer.id).exists())
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists()) 

