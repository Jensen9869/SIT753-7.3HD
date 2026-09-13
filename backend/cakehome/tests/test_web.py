import pytest

from cakehome.models import Order


@pytest.mark.django_db
class TestMenuPage:
    def test_lists_available_cakes(self, client, cake):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Vanilla Sponge" in response.content

    def test_hides_unavailable_cakes(self, client, cake):
        cake.is_available = False
        cake.save()
        response = client.get("/")
        assert b"Vanilla Sponge" not in response.content

    def test_shows_empty_message_with_no_cakes(self, client, db):
        response = client.get("/")
        assert b"Nothing is on the board" in response.content

    def test_places_an_order_and_redirects(self, client, cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St, Carnegie",
            "delivery_distance_km": "5",
            f"size_{cake.id}": "small",
            f"qty_{cake.id}": "2",
        })
        assert response.status_code == 302
        order = Order.objects.get()
        assert response.url == f"/orders/{order.id}/?placed=1"
        assert order.item_count == 2

    def test_rejects_an_empty_basket(self, client, cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "5",
            f"qty_{cake.id}": "0",
        })
        assert response.status_code == 200
        assert b"at least one cake" in response.content
        assert Order.objects.count() == 0

    def test_rejects_distance_beyond_range(self, client, cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "99",
            f"size_{cake.id}": "small",
            f"qty_{cake.id}": "1",
        })
        assert b"up to 40 km" in response.content
        assert Order.objects.count() == 0

    def test_rejects_unreadable_distance(self, client, cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "five",
            f"size_{cake.id}": "small",
            f"qty_{cake.id}": "1",
        })
        assert b"as a number" in response.content

    def test_reports_insufficient_stock(self, client, sold_out_cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "5",
            f"size_{sold_out_cake.id}": "small",
            f"qty_{sold_out_cake.id}": "1",
        })
        assert b"Not enough stock" in response.content

    def test_ignores_a_non_numeric_quantity(self, client, cake):
        response = client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "5",
            f"qty_{cake.id}": "lots",
        })
        assert b"at least one cake" in response.content


@pytest.mark.django_db
class TestOrderPages:
    @pytest.fixture
    def order(self, client, cake):
        client.post("/", {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St",
            "delivery_distance_km": "5",
            f"size_{cake.id}": "medium",
            f"qty_{cake.id}": "1",
        })
        return Order.objects.get()

    def test_detail_shows_the_order(self, client, order):
        response = client.get(f"/orders/{order.id}/")
        assert response.status_code == 200
        assert b"Vanilla Sponge" in response.content
        assert b"Order received" in response.content

    def test_detail_confirms_a_new_order(self, client, order):
        response = client.get(f"/orders/{order.id}/?placed=1")
        assert b"your order is in" in response.content

    def test_detail_marks_reached_steps(self, client, order):
        order.transition_to("confirmed")
        response = client.get(f"/orders/{order.id}/")
        body = response.content.decode()
        assert body.count('class="done"') >= 2

    def test_detail_shows_cancellation(self, client, order):
        order.transition_to("cancelled")
        response = client.get(f"/orders/{order.id}/")
        assert b"Cancelled" in response.content

    def test_detail_404_for_unknown_order(self, client, db):
        assert client.get("/orders/9999/").status_code == 404

    def test_list_shows_orders(self, client, order):
        response = client.get("/orders/")
        assert response.status_code == 200
        assert b"Jia" in response.content

    def test_list_is_empty_without_orders(self, client, db):
        response = client.get("/orders/")
        assert b"No orders yet" in response.content