from rest_framework import viewsets, status 
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action  
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Book
from .serializers import *


class AddBookToStore(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUser]  

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:  
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    # Filter book list by author    
    @action(detail=False, methods=['get'])
    def by_author(self, request):
        author = request.query_params.get('author')
    
        if author:
           books = Book.objects.filter(author__icontains=author)
        else:
           books = Book.objects.all()
    
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    # Filter book list by genre    
    @action(detail=False, methods=['get'])
    def by_genre(self, request):
        genre = request.query_params.get('genre')

        if genre:
           books = Book.objects.filter(genre__icontains=genre)
        else:
           books = Book.objects.all()

        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
        return Response({"detail": "Genre not provided"}, status=400)

    # Search book by title
    @action(detail=False, methods=['get'])
    def search(self, request):
        title = request.query_params.get('title')
        if title:
            books = Book.objects.filter(title__icontains=title)
            serializer = self.get_serializer(books, many=True)
            return Response(serializer.data)
        return Response({"detail": "Title not provided"}, status=400)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()  
        return super().get_queryset().filter(user=self.request.user)

    # Only Unautharized user can create new profile
    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            raise PermissionDenied("Вы уже вошли в систему и не можете создать новый аккаунт.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        customer = self.get_object()
        if customer.user != request.user and not request.user.is_staff:
            return Response({"error": "You can only update your own profile."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(customer, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        customer = self.get_object()
        if customer.user != request.user and not request.user.is_staff:
            return Response({"error": "You can only update your own profile."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()
        if customer.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not have permission to delete this profile."}, status=status.HTTP_403_FORBIDDEN)

        user = customer.user
        response = super().destroy(request, *args, **kwargs)
        user.delete()
        return Response({"detail": "Customer successfully deleted."}, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        book_id = self.request.data.get('book')
        book = get_object_or_404(Book, id=book_id)
        existing_review = Review.objects.filter(book=book, user=self.request.user).first()
        
        if existing_review:
            return Response({"error": "You have already reviewed this book."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save(user=self.request.user, book=book)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user:
            return Response({"error": "You can only update your own review."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user:
            return Response({"error": "You can only delete your own review."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    # Current user reviews list
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_reviews(self, request):
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    # Get user reviews for admin
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def user_reviews(self, request, pk=None):
        customer = get_object_or_404(Customer, pk=pk)
        reviews = Review.objects.filter(user=customer.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    # Get book reviews for everyone 
    @action(detail=True, methods=['get'], permission_classes=[])
    def book_reviews(self, request, pk=None):
        book = get_object_or_404(Book, pk=pk)
        reviews = Review.objects.filter(book=book)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Cart.objects.all()   
        return Cart.objects.filter(customer=self.request.user.customer) 

    def check_object_permissions(self, request, cart_item):
        if cart_item.customer != request.user.customer or request.user.is_staff:
            return False  
        return True  

    # Add book to cart. If book already in cart, add 1 to quantity. Else just add a book
    def create(self, request, *args, **kwargs):
        customer = request.user.customer
        book_id = request.data.get('book_id')

        try:
            # Проверяем, есть ли эта книга уже в корзине пользователя
            cart_item = Cart.objects.get(customer=customer, book_id=book_id)
            # Если книга есть, увеличиваем количество на 1 и вызываем метод update
            updated_quantity = cart_item.quantity + 1
            return self.update_quantity(cart_item, updated_quantity)  # Вызываем метод update_quantity
        except Cart.DoesNotExist:
            # Если книги нет в корзине, создаем новый элемент корзины с количеством 1
            cart_item = Cart.objects.create(customer=customer,book_id=book_id,quantity=1)
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    # You can only update quantity by Patch/Put for this API Enpoint        
    def update(self, request, *args, **kwargs):
        """Обновление количества единиц книги в корзине (доступно только владельцу корзины)"""
        cart_item = self.get_object()

        # Проверка прав на обновление (только владелец корзины)
        if not self.check_object_permissions(request, cart_item):
            raise PermissionDenied("Permission denied.")

        # Обновляем количество единиц книги
        updated_quantity = request.data.get('quantity', cart_item.quantity)
        return self.update_quantity(cart_item, updated_quantity)

    def update_quantity(self, cart_item, quantity):
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        cart_item = self.get_object()

        if not self.check_object_permissions(request, cart_item):
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['delete'], url_path='clear-cart')
    def clear_cart(self, request):
        if request.user.is_staff:
            return Response({"error": "Admins cannot modify carts."}, status=status.HTTP_403_FORBIDDEN)

        Cart.objects.filter(customer=request.user.customer).delete()  # Удаляем все элементы корзины пользователя
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Get user cart for Admin    
    @action(detail=False, methods=['get'], url_path='user-cart/(?P<user_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def user_cart(self, request, user_id=None):
        if not request.user.is_staff:
            return Response({"error": "Only admins can view other users' carts."}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer = Customer.objects.get(user__id=user_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_items = Cart.objects.filter(customer=customer)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # You can see your orders as customer. You can see all orders as an admin. 
    # You can filter orders lisr by user and by status
    def get_queryset(self):
        queryset = Order.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(customer=self.request.user.customer)
        else:
            customer_id = self.request.query_params.get('customer_id')
            status = self.request.query_params.get('status')

            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
            if status:
                queryset = queryset.filter(status=status)

        return queryset

    # You can get a specific order    
    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()

        if order.customer != request.user.customer and not request.user.is_staff:
            return Response({"error": "You do not have permission to view this order."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    # Create order from cart items    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_order(self, request):
        customer = request.user.customer
        cart_items = Cart.objects.filter(customer=customer)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(customer=customer, discount=0.00)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                book=item.book,
                quantity=item.quantity,
                price=item.book.price,
                discount=item.book.discount,
            )

        order.total_price = order.calculate_total()
        order.save()

        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # You can update only order status by this endpoint. Only admin can update status
    def update(self, request, *args, **kwargs):
        order = self.get_object()

        if not request.user.is_staff:
            return Response({"error": "You do not have permission to update this order."}, status=status.HTTP_403_FORBIDDEN)

        if 'status' not in request.data or len(request.data) > 1:
            return Response({"error": "Only the status field can be updated."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
