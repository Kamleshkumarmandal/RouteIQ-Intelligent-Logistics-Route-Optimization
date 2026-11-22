import unittest

from routeiq.engine import NODES, ROAD_EDGES, build_graph, haversine_km, plan_fleet, shortest_path


class RouteEngineTests(unittest.TestCase):
    def test_dijkstra_returns_valid_shortest_path(self):
        result = shortest_path("depot", "tambaram")
        self.assertEqual(result["path"][0], "depot")
        self.assertEqual(result["path"][-1], "tambaram")
        self.assertGreater(result["distance_km"], 0)
        self.assertLessEqual(
            result["distance_km"],
            sum(edge[2] for edge in ROAD_EDGES),
        )

    def test_same_node_has_zero_distance(self):
        result = shortest_path("depot", "depot")
        self.assertEqual(result["path"], ["depot"])
        self.assertEqual(result["distance_km"], 0)

    def test_unknown_node_is_rejected(self):
        with self.assertRaises(ValueError):
            shortest_path("not-a-node", "depot")

    def test_graph_rejects_bad_edges(self):
        with self.assertRaises(ValueError):
            build_graph([("depot", "not-a-node", 2)])
        with self.assertRaises(ValueError):
            build_graph([("depot", "anna_nagar", 0)])

    def test_haversine_is_positive_for_different_nodes(self):
        self.assertGreater(haversine_km("depot", "adyar"), 0)
        self.assertEqual(haversine_km("depot", "depot"), 0)

    def test_dispatch_obeys_vehicle_capacity(self):
        orders = [
            {"id": "A", "destination": "anna_nagar", "load": 2, "priority": 3, "deadline": "10:00"},
            {"id": "B", "destination": "adyar", "load": 2, "priority": 2, "deadline": "11:00"},
            {"id": "C", "destination": "tambaram", "load": 2, "priority": 1, "deadline": "12:00"},
        ]
        vehicles = [
            {"id": "V1", "driver": "Maya", "capacity": 3},
            {"id": "V2", "driver": "Arun", "capacity": 3},
        ]
        plans = plan_fleet(orders, vehicles, traffic_factor=1.2)
        assigned = [order_id for plan in plans for order_id in plan["order_ids"]]
        self.assertCountEqual(assigned, ["A", "B", "C"])
        self.assertTrue(all(plan["used_capacity"] <= plan["capacity"] for plan in plans))
        self.assertTrue(all(plan["estimated_minutes"] > 0 for plan in plans))

    def test_capacity_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "capacity"):
            plan_fleet(
                [{"id": "A", "destination": "adyar", "load": 10}],
                [{"id": "V1", "driver": "Maya", "capacity": 2}],
            )

    def test_traffic_increases_eta(self):
        order = [{"id": "A", "destination": "adyar", "load": 1}]
        vehicle = [{"id": "V1", "driver": "Maya", "capacity": 2}]
        normal = plan_fleet(order, vehicle, traffic_factor=1.0)[0]
        traffic = plan_fleet(order, vehicle, traffic_factor=1.5)[0]
        self.assertGreater(traffic["estimated_minutes"], normal["estimated_minutes"])


if __name__ == "__main__":
    unittest.main()
