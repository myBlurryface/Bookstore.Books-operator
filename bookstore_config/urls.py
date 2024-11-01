from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from books_operator.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Use python3 manage.py show_urls to see urlpatterns for router
router = DefaultRouter()
router.register(r'books', AddBookToStore, basename='books')
router.register(r'customer', CustomerViewSet, basename='customer')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]