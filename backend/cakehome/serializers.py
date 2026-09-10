from rest_framework import serializers
from .models import Cake, Category, Order, OrderItem

from decimal import Decimal

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]

class CakeSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Cake
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "stock",
            "is_available",
            "created_at",
            "in_stock",
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    cake_name = serializers.CharField(source="cake.name", read_only=True)
 
    class Meta:
        model = OrderItem
        fields = ["id", "cake", "cake_name", "size", "quantity",
                  "unit_price", "line_total"]
 
 
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
 
    class Meta:
        model = Order
        fields = [
            "id", "customer_name", "customer_email", "delivery_address",
            "delivery_distance_km", "status", "subtotal", "delivery_fee",
            "total", "item_count", "items", "created_at",
        ]
 
 
class OrderItemInputSerializer(serializers.Serializer):
    """One line of an incoming order request."""
    cake_id = serializers.IntegerField()
    size = serializers.ChoiceField(choices=["small", "medium", "large"])
    quantity = serializers.IntegerField(min_value=1, max_value=50)
 
 
class OrderCreateSerializer(serializers.Serializer):
    """Validates the shape of an incoming order before any database work."""
    customer_name = serializers.CharField(max_length=120)
    customer_email = serializers.EmailField()
    delivery_address = serializers.CharField()
    delivery_distance_km = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0.00"), max_value=Decimal("40.00")
    )
    items = OrderItemInputSerializer(many=True, allow_empty=False)