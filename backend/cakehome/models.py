from django.db import models

from .services import can_transition
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Cake(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="cakes"
    )
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["name"]
 
    def __str__(self):
        return self.name
 
    @property
    def in_stock(self):
        return self.is_available and self.stock > 0

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("baking", "Baking"),
        ("ready", "Ready"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()

    delivery_address = models.TextField()
    delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2)

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.pk} by {self.customer_name} ({self.status})"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def transition_to(self, new_status):
        if not can_transition(self.status, new_status):
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")

        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
        return self

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    cake = models.ForeignKey(Cake, on_delete=models.PROTECT, related_name="order_items")

    size = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField()


    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.cake.name} ({self.size})"