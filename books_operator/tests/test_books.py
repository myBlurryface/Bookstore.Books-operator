from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from books_operator.models import User, Book 


class BookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='password')

        self.book_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'description': 'Test description',
            'synopsis': 'Test synopsis',
            'genre': 'Test genre',
            'price': '19.99',
            'discount': '0.00',
            'stock': 10
        }

        self.book_data_1 = {
            'title': 'Another Book', 
            'author': 'Another Author', 
            'description': 'Another description', 
            'synopsis': 'Another synopsis', 
            'genre': 'Science Fiction', 
            'price': '29.99', 
            'discount': '5.00', 
            'stock': 5
        }
    
        self.user_token = str(AccessToken.for_user(self.user))
        self.admin_token = str(AccessToken.for_user(self.admin_user))

        self.client = APIClient()

    def api_authentication(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_book_as_admin(self):
        self.api_authentication(self.admin_token)

        url = reverse('books-list')

        response = self.client.post(url, self.book_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)

    def test_create_book_as_non_admin(self):
        self.api_authentication(self.user_token)

        url = reverse('books-list')

        response = self.client.post(url, self.book_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  

    def test_update_book_as_admin(self):
        self.api_authentication(self.admin_token)

        book = Book.objects.create(**self.book_data)
        updated_data = self.book_data.copy()
        updated_data['title'] = 'Updated Test Book'

        url = reverse('books-detail', args=[book.id])

        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Book.objects.get(id=book.id).title, 'Updated Test Book')

    def test_update_book_as_non_admin(self):
        self.api_authentication(self.user_token)

        book = Book.objects.create(**self.book_data)
        updated_data = self.book_data.copy()
        updated_data['title'] = 'Updated Test Book'

        url = reverse('books-detail', args=[book.id])

        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 

    def test_delete_book_as_admin(self):
        self.api_authentication(self.admin_token)

        book = Book.objects.create(**self.book_data)

        url = reverse('books-detail', args=[book.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Book.objects.count(), 0)

    def test_delete_book_as_non_admin(self):
        self.api_authentication(self.user_token)

        book = Book.objects.create(**self.book_data)
        url = reverse('books-detail', args=[book.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 

    def test_filter_books_by_genre(self):
        Book.objects.create(**self.book_data)
        Book.objects.create(**self.book_data_1)

        url = reverse('books-by-genre')  

        response = self.client.get(url, {'genre': 'Fantasy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
    
        response = self.client.get(url, {'genre': 'Fiction'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['genre'], 'Science Fiction')

    def test_filter_books_by_author(self):
        Book.objects.create(**self.book_data)
        Book.objects.create(**self.book_data_1)

        url = reverse('books-by-author') 

        response = self.client.get(url, {'author': 'Test Author'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['author'], 'Test Author')
    
        response = self.client.get(url, {'author': 'Test'}) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['author'], 'Test Author')

    def test_filter_books_by_title(self):
        Book.objects.create(**self.book_data)
        Book.objects.create(**self.book_data_1)

        url = reverse('books-search')  

        response = self.client.get(url, {'title': 'Test Book'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Book')
    
        response = self.client.get(url, {'title': 'Test'})   
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Book')

 
