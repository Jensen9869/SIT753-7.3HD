from django.contrib import admin

from .models import Category, Cake

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_available", "created_at")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "is_available")
