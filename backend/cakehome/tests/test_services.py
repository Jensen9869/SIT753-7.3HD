from decimal import Decimal

import pytest

from cakehome.services import (
    calculate_item_price,
    calculate_delivery_fee,
    calculate_order_total,
    check_stock,
    can_transition,
)

from cakehome.models import Cake, Category


class TestItemPrice:
    def test_small_is_base_price(self):
        assert calculate_item_price("40.00", "small", 1) == Decimal("40.00")

    def test_medium_adds_half(self):
        assert calculate_item_price("40.00", "medium", 1) == Decimal("60.00")

    def test_quantity_multiplies(self):
        assert calculate_item_price("40.00", "large", 3) == Decimal("264.00")

    def test_rounds_to_cents(self):
        assert calculate_item_price("33.33", "medium", 1) == Decimal("50.00")

    def test_rejects_zero_quantity(self):
        with pytest.raises(ValueError):
            calculate_item_price("40.00", "small", 0)

    def test_rejects_unknown_size(self):
        with pytest.raises(ValueError):
            calculate_item_price("40.00", "enormous", 1)


class TestDeliveryFee:
    def test_base_plus_distance(self):
        assert calculate_delivery_fee("50.00", 4) == Decimal("14.00")

    def test_free_above_threshold(self):
        assert calculate_delivery_fee("100.00", 20) == Decimal("0.00")

    def test_just_below_threshold_still_charged(self):
        assert calculate_delivery_fee("99.99", 2) == Decimal("12.00")

    def test_rejects_negative_distance(self):
        with pytest.raises(ValueError):
            calculate_delivery_fee("50.00", -1)

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            calculate_delivery_fee("50.00", 45)


class TestStock:
    def test_enough(self):
        assert check_stock(10, 3) is True

    def test_exact(self):
        assert check_stock(3, 3) is True

    def test_not_enough(self):
        assert check_stock(2, 3) is False

    def test_rejects_zero_request(self):
        with pytest.raises(ValueError):
            check_stock(10, 0)


class TestStatusTransitions:
    def test_pending_to_confirmed(self):
        assert can_transition("pending", "confirmed") is True

    def test_cannot_skip_stages(self):
        assert can_transition("pending", "delivered") is False

    def test_delivered_is_terminal(self):
        assert can_transition("delivered", "baking") is False

    def test_can_cancel_before_ready(self):
        assert can_transition("baking", "cancelled") is True

    def test_rejects_unknown_status(self):
        with pytest.raises(ValueError):
            can_transition("frozen", "confirmed")


class TestOrderTotal:
    def test_single_item_with_delivery(self):
        result = calculate_order_total(
            [{"base_price": "40.00", "size": "small", "quantity": 1}], 4
        )
        assert result["subtotal"] == Decimal("40.00")
        assert result["delivery_fee"] == Decimal("14.00")
        assert result["total"] == Decimal("54.00")

    def test_large_order_gets_free_delivery(self):
        result = calculate_order_total(
            [{"base_price": "40.00", "size": "large", "quantity": 2}], 10
        )
        assert result["delivery_fee"] == Decimal("0.00")
        assert result["total"] == Decimal("176.00")

    def test_rejects_empty_order(self):
        with pytest.raises(ValueError):
            calculate_order_total([], 5)

@pytest.mark.django_db
class TestCake:
    def test_in_stock_true(self):
        cat = Category.objects.create(name="Sponge", slug="sponge")
        cake = Cake.objects.create(name="Vanilla", price=Decimal("40.00"),
                                   category=cat, stock=5, is_available=True)
        assert cake.in_stock is True

    def test_out_of_stock_when_zero(self):
        cat = Category.objects.create(name="Tart", slug="tart")
        cake = Cake.objects.create(name="Lemon", price=Decimal("35.00"),
                                   category=cat, stock=0, is_available=True)
        assert cake.in_stock is False

    def test_unavailable_is_not_in_stock(self):
        cat = Category.objects.create(name="Mousse", slug="mousse")
        cake = Cake.objects.create(name="Choc", price=Decimal("50.00"),
                                   category=cat, stock=10, is_available=False)
        assert cake.in_stock is False

    def test_str(self):
        cat = Category.objects.create(name="Cheesecake", slug="cheesecake")
        assert str(cat) == "Cheesecake"