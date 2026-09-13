"""
The customer-facing pages.

These are kept apart from views.py, which serves the JSON API. Both call the
same place_order() service, so the pricing and stock rules cannot drift
between the website and the API.
"""

from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404, redirect, render

from .models import Cake, Order
from .ordering import OrderError, place_order

# The order a cake moves through, used to draw the tracker.
TRACK_STEPS = [
    ("pending", "Order received"),
    ("confirmed", "Confirmed by the shop"),
    ("baking", "In the oven"),
    ("ready", "Ready for delivery"),
    ("delivered", "Delivered"),
]


def _build_track(order):
    """Mark every step up to and including the current one as done."""
    if order.status == "cancelled":
        return [{"label": "Cancelled", "done": True, "cancelled": True}]

    reached = [key for key, _ in TRACK_STEPS].index(order.status)
    return [
        {"label": label, "done": index <= reached, "cancelled": False}
        for index, (_, label) in enumerate(TRACK_STEPS)
    ]


def _read_basket(post_data, cakes):
    """Pull the quantities the customer typed into the menu."""
    basket = []
    for cake in cakes:
        try:
            quantity = int(post_data.get(f"qty_{cake.id}", 0))
        except ValueError:
            continue
        if quantity > 0:
            basket.append({
                "cake_id": cake.id,
                "size": post_data.get(f"size_{cake.id}", "small"),
                "quantity": quantity,
            })
    return basket


def menu(request):
    cakes = Cake.objects.select_related("category").filter(is_available=True)

    if request.method != "POST":
        return render(request, "cakehome/menu.html",
                      {"cakes": cakes, "page": "menu"})

    basket = _read_basket(request.POST, cakes)
    error = None

    if not basket:
        error = "Choose at least one cake before placing the order."
    else:
        try:
            distance = Decimal(request.POST.get("delivery_distance_km", "0"))
        except InvalidOperation:
            distance = None
            error = "Enter the delivery distance as a number, for example 5.5."

        if distance is not None and not (0 <= distance <= 40):
            error = "We deliver up to 40 km from the shop."
        elif distance is not None:
            try:
                order = place_order(
                    customer_name=request.POST.get("customer_name", "").strip(),
                    customer_email=request.POST.get("customer_email", "").strip(),
                    delivery_address=request.POST.get("delivery_address", "").strip(),
                    delivery_distance_km=distance,
                    items=basket,
                )
                return redirect(f"/orders/{order.id}/?placed=1")
            except (OrderError, ValueError) as exc:
                error = str(exc)

    return render(request, "cakehome/menu.html", {
        "cakes": cakes,
        "page": "menu",
        "error": error,
        "form_data": request.POST,
    })


def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__cake"), pk=pk
    )
    return render(request, "cakehome/order_detail.html", {
        "order": order,
        "track": _build_track(order),
        "just_placed": request.GET.get("placed") == "1",
        "page": "orders",
    })


def order_list(request):
    return render(request, "cakehome/order_list.html", {
        "orders": Order.objects.all()[:50],
        "page": "orders",
    })