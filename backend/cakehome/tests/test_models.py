from decimal import Decimal

import pytest

from cakehome.models import Order


@pytest.mark.django_db
class TestCake:
    def test_in_stock_when_available_with_stock(self, cake):
        assert cake.in_stock is True

    def test_out_of_stock_when_zero(self, sold_out_cake):
        assert sold_out_cake.in_stock is False

    def test_unavailable_is_never_in_stock(self, cake):
        cake.is_available = False
        assert cake.in_stock is False

    def test_str(self, cake):
        assert str(cake) == "Vanilla Sponge"


@pytest.mark.django_db
class TestCategory:
    def test_str(self, category):
        assert str(category) == "Sponge"


@pytest.mark.django_db
class TestOrderTransitions:
    @pytest.fixture
    def order(self):
        return Order.objects.create(
            customer_name="Jia",
            customer_email="jia@example.com",
            delivery_address="1 Test St",
            delivery_distance_km=Decimal("5.00"),
        )

    def test_starts_pending(self, order):
        assert order.status == "pending"

    def test_can_confirm(self, order):
        order.transition_to("confirmed")
        order.refresh_from_db()
        assert order.status == "confirmed"

    def test_cannot_skip_to_delivered(self, order):
        with pytest.raises(ValueError):
            order.transition_to("delivered")

    def test_delivered_is_terminal(self, order):
        for step in ["confirmed", "baking", "ready", "delivered"]:
            order.transition_to(step)
        with pytest.raises(ValueError):
            order.transition_to("baking")

    def test_str(self, order):
        assert "Jia" in str(order)
        assert "pending" in str(order)