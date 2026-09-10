"""
Order placement.

This module is the seam between the pure business rules in services.py and
the database. Keeping it separate means services.py stays testable without
Django, while this file holds the parts that need a transaction.
"""

from django.db import transaction

from .models import Cake, Order, OrderItem
from .services import (
    calculate_delivery_fee,
    calculate_item_price,
    check_stock,
)


class OrderError(Exception):
    """Raised when an order cannot be placed."""


@transaction.atomic
def place_order(customer_name, customer_email, delivery_address,
                delivery_distance_km, items):
    """
    Create an order and reserve stock.

    items is a list of dicts with keys: cake_id, size, quantity.

    The whole thing runs in one transaction, so a failure on the last item
    leaves no half-created order and no stock reserved.
    """
    if not items:
        raise OrderError("An order must contain at least one item")

    # select_for_update locks the rows so two customers cannot both take
    # the last cake.
    cake_ids = [item["cake_id"] for item in items]
    cakes = {
        cake.id: cake
        for cake in Cake.objects.select_for_update().filter(id__in=cake_ids)
    }

    missing = set(cake_ids) - set(cakes)
    if missing:
        raise OrderError(f"Unknown cake id(s): {sorted(missing)}")

    subtotal = 0
    lines = []

    for item in items:
        cake = cakes[item["cake_id"]]

        if not cake.is_available:
            raise OrderError(f"{cake.name} is not currently available")

        if not check_stock(cake.stock, item["quantity"]):
            raise OrderError(
                f"Not enough stock for {cake.name}: "
                f"{cake.stock} available, {item['quantity']} requested"
            )

        line_total = calculate_item_price(cake.price, item["size"], item["quantity"])
        unit_price = line_total / item["quantity"]
        subtotal += line_total

        lines.append({
            "cake": cake,
            "size": item["size"],
            "quantity": item["quantity"],
            "unit_price": unit_price,
            "line_total": line_total,
        })

    delivery_fee = calculate_delivery_fee(subtotal, delivery_distance_km)

    order = Order.objects.create(
        customer_name=customer_name,
        customer_email=customer_email,
        delivery_address=delivery_address,
        delivery_distance_km=delivery_distance_km,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=subtotal + delivery_fee,
    )

    for line in lines:
        OrderItem.objects.create(
            order=order,
            cake=line["cake"],
            size=line["size"],
            quantity=line["quantity"],
            unit_price=line["unit_price"],
            line_total=line["line_total"],
        )
        # reserve the stock
        line["cake"].stock -= line["quantity"]
        line["cake"].save(update_fields=["stock"])

    return order