from decimal import Decimal

import pytest

from cakehome.models import Order
from cakehome.ordering import OrderError, place_order


@pytest.mark.django_db
class TestPlaceOrder:
    def test_creates_order_with_correct_totals(self, cake):
        order = place_order(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("5"),
            items=[{"cake_id": cake.id, "size": "small", "quantity": 1}],
        )
        # 40.00 small, delivery 10 + 1 x 5 = 15
        assert order.subtotal == Decimal("40.00")
        assert order.delivery_fee == Decimal("15.00")
        assert order.total == Decimal("55.00")

    def test_size_multiplier_is_applied(self, cake):
        order = place_order(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("2"),
            items=[{"cake_id": cake.id, "size": "medium", "quantity": 2}],
        )
        # 40 x 1.5 x 2 = 120, over the free delivery threshold
        assert order.subtotal == Decimal("120.00")
        assert order.delivery_fee == Decimal("0.00")

    def test_reserves_stock(self, cake):
        place_order(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("3"),
            items=[{"cake_id": cake.id, "size": "small", "quantity": 4}],
        )
        cake.refresh_from_db()
        assert cake.stock == 6

    def test_creates_order_items(self, cake):
        order = place_order(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("3"),
            items=[{"cake_id": cake.id, "size": "large", "quantity": 2}],
        )
        assert order.items.count() == 1
        line = order.items.first()
        assert line.size == "large"
        assert line.quantity == 2
        assert line.line_total == Decimal("176.00")   # 40 x 2.2 x 2

    def test_item_count_property(self, cake):
        order = place_order(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("3"),
            items=[{"cake_id": cake.id, "size": "small", "quantity": 3}],
        )
        assert order.item_count == 3

    def test_rejects_empty_order(self):
        with pytest.raises(OrderError):
            place_order(
                customer_name="Jia",
                customer_email="jia@example.com",
                delivery_address="1 Test St",
                delivery_distance_km=Decimal("3"),
                items=[],
            )

    def test_rejects_unknown_cake(self, cake):
        with pytest.raises(OrderError):
            place_order(
                customer_name="Jia",
                customer_email="jia@example.com",
                delivery_address="1 Test St",
                delivery_distance_km=Decimal("3"),
                items=[{"cake_id": 99999, "size": "small", "quantity": 1}],
            )

    def test_rejects_insufficient_stock(self, sold_out_cake):
        with pytest.raises(OrderError):
            place_order(
                customer_name="Jia",
                customer_email="jia@example.com",
                delivery_address="1 Test St",
                delivery_distance_km=Decimal("3"),
                items=[{"cake_id": sold_out_cake.id, "size": "small", "quantity": 1}],
            )

    def test_rejects_unavailable_cake(self, cake):
        cake.is_available = False
        cake.save()
        with pytest.raises(OrderError):
            place_order(
                customer_name="Jia",
                customer_email="jia@example.com",
                delivery_address="1 Test St",
                delivery_distance_km=Decimal("3"),
                items=[{"cake_id": cake.id, "size": "small", "quantity": 1}],
            )

    def test_failed_order_leaves_no_trace(self, cake, sold_out_cake):
        """A failure on the second line must roll the whole order back."""
        with pytest.raises(OrderError):
            place_order(
                customer_name="Jia",
                customer_email="jia@example.com",
                delivery_address="1 Test St",
                delivery_distance_km=Decimal("3"),
                items=[
                    {"cake_id": cake.id, "size": "small", "quantity": 1},
                    {"cake_id": sold_out_cake.id, "size": "small", "quantity": 1},
                ],
            )
        assert Order.objects.count() == 0
        cake.refresh_from_db()
        assert cake.stock == 10          # stock was not touched