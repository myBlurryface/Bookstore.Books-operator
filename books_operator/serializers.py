from rest_framework import serializers
from .models import *

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    spent_money = serializers.DecimalField(source='total_spent', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'phone_number', 'spent_money']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')
        if request and not request.user.is_staff:
            representation.pop('id', None)
        
        return representation

    def validate_username(self, value):
        if self.instance:
            # Username doesn't exists in database, when you update username for exist user
            if self.instance.user.username != value and User.objects.filter(username=value).exists():
                raise serializers.ValidationError("This username already taken.")
            # Username doesn't exists in database, when add new user
        elif User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username already taken.")
        return value

    def validate_phone_number(self, value):
        if self.instance:
            # Phone number doesn't exists in database, when you update Phone number for exist user
            if self.instance.phone_number != value and Customer.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("This phone number already exists.")
            # Phone number doesn't exists in database, when add new user    
        elif Customer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number already exists.")
        return value

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'book', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['book_title'] = instance.book.title  
        representation['user_name'] = instance.user.username  
        return representation


class CartSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.user', read_only=True)
    book_id = serializers.IntegerField()
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_price = serializers.DecimalField(source='book.price', max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False)
    discount = serializers.DecimalField(source='book.discount', max_digits=5, decimal_places=2, read_only=True, coerce_to_string=False)  
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False) 
    added_at = serializers.DateTimeField(read_only=True) 
    class Meta:
        model = Cart
        fields = ['id', 'customer', 'book_id', 'book_title', 'book_price', 'quantity', 'discount', 'total_price', 'added_at']
        read_only_fields = ['id', 'customer', 'book_title', 'book_price', 'discount', 'total_price', 'added_at', 'book_id'] 

    def get_total_price(self, obj):
        return (obj.book.price * obj.quantity) * (1 - obj.discount / 100)

    def validate_book_id(self, value):
        # Book must exist in database
        if not Book.objects.filter(id=value).exists():
            raise serializers.ValidationError("The book with the specified ID does not exist.")
        return value

    # Bind book and cart record
    def create(self, validated_data):
        book_id = validated_data.pop('book_id')
        validated_data['book'] = Book.objects.get(id=book_id)  
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if request and not request.user.is_staff:
            representation.pop('book_id')
            representation.pop('id')
        
        return representation

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['book', 'quantity', 'price', 'discount']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'created_at', 'updated_at', 'status', 'total_price', 'discount', 'items']
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at', 'total_price']