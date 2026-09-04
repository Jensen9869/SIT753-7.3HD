from rest_framework import serializers
from .models import Cake, Category





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