import unittest

from fastapi.testclient import TestClient

from routeiq.api import app


class RouteApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_locations(self):
        response = self.client.get("/api/v1/locations")
        self.assertEqual(response.status_code, 200)
        self.assertIn("depot", response.json()["locations"])

    def test_route_endpoint(self):
        response = self.client.post("/api/v1/route", json={"start": "depot", "destination": "adyar"})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["distance_km"], 0)
        self.assertEqual(response.json()["data_source"], "illustrative_demo_road_graph")

    def test_unknown_location_is_rejected(self):
        response = self.client.post("/api/v1/route", json={"start": "depot", "destination": "somewhere"})
        self.assertEqual(response.status_code, 422)

    def test_dispatch_endpoint(self):
        response = self.client.post("/api/v1/dispatch", json={
            "orders": [{"id": "O1", "destination": "adyar", "load": 1, "priority": 4}],
            "vehicles": [{"id": "V1", "driver": "Demo Driver", "capacity": 3}],
            "traffic_factor": 1.2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["plans"][0]["order_ids"], ["O1"])


if __name__ == "__main__":
    unittest.main()
