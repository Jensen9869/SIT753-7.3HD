from django.contrib import admin

from .models import Category, Cake, Order, OrderItem

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

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price", "line_total")
 
 
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "status", "item_count",
                    "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "customer_email")
    readonly_fields = ("subtotal", "delivery_fee", "total", "created_at")
    inlines = [OrderItemInline]
