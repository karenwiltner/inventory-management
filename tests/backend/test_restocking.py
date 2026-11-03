"""
Tests for restocking API endpoints.
"""
from datetime import datetime

import pytest

import main


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    """Submitted orders live in a module-level list, so reset it to keep tests independent."""
    main.restocking_orders.clear()
    yield
    main.restocking_orders.clear()


def get_forecasts_by_sku(client):
    """Helper: demand forecasts keyed by SKU."""
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_demand_forecasts_include_restocking_fields(self, client):
        """Test that demand forecasts expose the cost, stock and lead time used for restocking."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["quantity_on_hand"], int)
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["quantity_on_hand"] >= 0
            assert forecast["lead_time_days"] > 0

    def test_get_restocking_orders_empty(self, client):
        """Test that no orders are listed before anything is submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client):
        """Test submitting a valid restocking order."""
        forecasts = get_forecasts_by_sku(client)
        sku = "WDG-001"

        response = client.post(
            "/api/restocking/orders",
            json={"budget": 10000, "items": [{"sku": sku, "quantity": 100}]},
        )
        assert response.status_code == 200

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["budget"] == 10000
        assert len(order["items"]) == 1

        item = order["items"][0]
        assert item["sku"] == sku
        assert item["name"] == forecasts[sku]["item_name"]
        assert item["quantity"] == 100
        assert item["unit_cost"] == forecasts[sku]["unit_cost"]

    def test_restocking_order_total_uses_server_prices(self, client):
        """Test that the order total is calculated from forecast unit costs."""
        forecasts = get_forecasts_by_sku(client)
        items = [{"sku": "WDG-001", "quantity": 100}, {"sku": "GSK-203", "quantity": 50}]

        response = client.post("/api/restocking/orders", json={"budget": 100000, "items": items})
        assert response.status_code == 200

        expected_total = sum(i["quantity"] * forecasts[i["sku"]]["unit_cost"] for i in items)
        assert abs(response.json()["total_value"] - expected_total) < 0.01

    def test_restocking_order_lead_time_is_longest_item(self, client):
        """Test that the order lead time equals the slowest item and sets the delivery date."""
        forecasts = get_forecasts_by_sku(client)
        items = [{"sku": "GSK-203", "quantity": 10}, {"sku": "CTL-330", "quantity": 1}]

        response = client.post("/api/restocking/orders", json={"budget": 100000, "items": items})
        assert response.status_code == 200

        order = response.json()
        expected_lead_time = max(forecasts[i["sku"]]["lead_time_days"] for i in items)
        assert order["lead_time_days"] == expected_lead_time

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == expected_lead_time

    def test_restocking_order_exceeding_budget_rejected(self, client):
        """Test that an order above the budget is rejected and not stored."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1, "items": [{"sku": "WDG-001", "quantity": 100}]},
        )
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

        assert client.get("/api/restocking/orders").json() == []

    def test_restocking_order_empty_items_rejected(self, client):
        """Test that an order without items is rejected."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_restocking_order_unknown_sku_rejected(self, client):
        """Test that an order with an unknown SKU is rejected."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "NOPE-000", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_restocking_order_non_positive_quantity_rejected(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        response = client.post(
            "/api/restocking/orders",
            json={"budget": 1000, "items": [{"sku": "WDG-001", "quantity": quantity}]},
        )
        assert response.status_code == 400

    def test_restocking_order_missing_budget_returns_validation_error(self, client):
        """Test that a malformed request body returns 422."""
        response = client.post(
            "/api/restocking/orders",
            json={"items": [{"sku": "WDG-001", "quantity": 1}]},
        )
        assert response.status_code == 422

    def test_get_restocking_orders_newest_first(self, client):
        """Test that submitted orders are listed newest first with incrementing numbers."""
        for sku in ["WDG-001", "GSK-203"]:
            response = client.post(
                "/api/restocking/orders",
                json={"budget": 10000, "items": [{"sku": sku, "quantity": 1}]},
            )
            assert response.status_code == 200

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        orders = response.json()
        assert [o["order_number"] for o in orders] == ["RST-0002", "RST-0001"]
        assert orders[0]["items"][0]["sku"] == "GSK-203"
