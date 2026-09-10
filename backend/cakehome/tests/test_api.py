import pytest


@pytest.mark.django_db
class TestHealth:
    def test_returns_ok(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": True}


@pytest.mark.django_db
class TestCakeApi:
    def test_lists_available_cakes(self, client, cake):
        response = client.get("/api/cakes/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_hides_unavailable_cakes(self, client, cake):
        cake.is_available = False
        cake.save()
        response = client.get("/api/cakes/")
        assert response.json()["count"] == 0

    def test_detail(self, client, cake):
        response = client.get(f"/api/cakes/{cake.id}/")
        assert response.status_code == 200
        assert response.json()["name"] == "Vanilla Sponge"


@pytest.mark.django_db
class TestOrderApi:
    def _payload(self, cake, **overrides):
        payload = {
            "customer_name": "Jia",
            "customer_email": "jia@example.com",
            "delivery_address": "1 Test St, Melbourne",
            "delivery_distance_km": "5.00",
            "items": [{"cake_id": cake.id, "size": "small", "quantity": 1}],
        }
        payload.update(overrides)
        return payload

    def test_places_an_order(self, client, cake):
        response = client.post(
            "/api/orders/", self._payload(cake),
            content_type="application/json",
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "pending"
        assert body["total"] == "55.00"
        assert len(body["items"]) == 1

    def test_rejects_bad_size(self, client, cake):
        payload = self._payload(cake)
        payload["items"][0]["size"] = "enormous"
        response = client.post("/api/orders/", payload,
                               content_type="application/json")
        assert response.status_code == 400

    def test_rejects_distance_out_of_range(self, client, cake):
        response = client.post(
            "/api/orders/", self._payload(cake, delivery_distance_km="99.00"),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_rejects_insufficient_stock(self, client, sold_out_cake):
        response = client.post(
            "/api/orders/", self._payload(sold_out_cake),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "stock" in response.json()["error"].lower()

    def test_rejects_empty_items(self, client, cake):
        response = client.post(
            "/api/orders/", self._payload(cake, items=[]),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_lists_orders(self, client, cake):
        client.post("/api/orders/", self._payload(cake),
                    content_type="application/json")
        response = client.get("/api/orders/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_advances_status(self, client, cake):
        created = client.post("/api/orders/", self._payload(cake),
                              content_type="application/json").json()
        response = client.post(
            f"/api/orders/{created['id']}/advance/",
            {"status": "confirmed"}, content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    def test_refuses_illegal_transition(self, client, cake):
        created = client.post("/api/orders/", self._payload(cake),
                              content_type="application/json").json()
        response = client.post(
            f"/api/orders/{created['id']}/advance/",
            {"status": "delivered"}, content_type="application/json",
        )
        assert response.status_code == 400

    def test_advance_requires_status(self, client, cake):
        created = client.post("/api/orders/", self._payload(cake),
                              content_type="application/json").json()
        response = client.post(
            f"/api/orders/{created['id']}/advance/", {},
            content_type="application/json",
        )
        assert response.status_code == 400