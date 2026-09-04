from decimal import Decimal, ROUND_HALF_UP

SIZE_MULTIPLIER = {
    "small": Decimal("1.0"),
    "medium": Decimal("1.5"),
    "large": Decimal("2.2"),
}

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"baking", "cancelled"},
    "baking": {"ready", "cancelled"},
    "ready": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}

FREE_DELIVERY_THRESHOLD = Decimal("100.00")
BASE_DELIVERY_FEE = Decimal("10.00")
PER_KM_FEE = Decimal("1.00")
MAX_DELIVERY_KM = Decimal("40")

def _money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_item_price(base_price, size, quantity):
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    if size not in SIZE_MULTIPLIER:
        raise ValueError(f"Unknown size: {size}")

    return _money(Decimal(base_price) * SIZE_MULTIPLIER[size] * quantity)

def calculate_delivery_fee(subtotal, distance_km):
    distance = Decimal(distance_km)
    if distance < 0:
        raise ValueError("Distance cannot be negative")
    if distance > MAX_DELIVERY_KM:
        raise ValueError(f"Distance cannot exceed {MAX_DELIVERY_KM} km")

    if Decimal(subtotal) >= FREE_DELIVERY_THRESHOLD:
        return Decimal("0.00")

    return _money(BASE_DELIVERY_FEE + (distance * PER_KM_FEE))

def check_stock(available, requested):
    if requested < 1:
        raise ValueError("Requested quantity must be at least 1")
    if available < requested:
        raise ValueError(f"Insufficient stock: {available} available, {requested} requested")

    return available >= requested

def can_transition(current, target):
    if current not in ALLOWED_TRANSITIONS:
        raise ValueError(f"Invalid current status: {current}")

    return target in ALLOWED_TRANSITIONS[current]


def calculate_order_total(items, delivery_distance_km):
    if not items:
        raise ValueError("Order must contain at least one item")
    
    subtotal = sum(
        calculate_item_price(item["base_price"], item["size"], item["quantity"])
        for item in items
    )

    delivery_fee = calculate_delivery_fee(subtotal, delivery_distance_km)
    total = subtotal + delivery_fee

    return {
        "subtotal": _money(subtotal),
        "delivery_fee": _money(delivery_fee),
        "total": _money(total),
    }
