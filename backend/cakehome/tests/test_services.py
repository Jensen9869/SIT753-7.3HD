from decimal import Decimal

import pytest

from cakehome.services import (
    calculate_item_price,
    calculate_delivery_fee,
    calculate_order_total,
    check_stock,
    can_transition,
)


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
        with pytest.raises(ValueError):
            check_stock(2, 3)

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