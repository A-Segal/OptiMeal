import unittest

from services.vrp.vrp_state import apply_move


class VrpStateTests(unittest.TestCase):
    def test_apply_move_orders_recipients_by_proximity(self):
        state = {
            "current_location": {"lat": 0.0, "lng": 0.0},
            "current_time": 0.0,
            "remaining_groups": [],
            "visited_groups": set(),
            "max_capacity": 10,
            "total_deliveries": 0,
            "route": [],
            "available_time": 1000.0,
        }

        group = {
            "center_id": 99,
            "center_lat": 0.0,
            "center_lng": 0.0,
            "assignment_ids": [1, 2, 3],
            "recipients_locations": [
                {"lat": 1.0, "lng": 0.0},
                {"lat": 0.0, "lng": 1.0},
                {"lat": 0.1, "lng": 0.1},
            ],
            "group_families": 3,
        }

        new_state = apply_move(state, group, 0.0)

        self.assertEqual(new_state["current_location"]["lat"], 0.0)
        self.assertEqual(new_state["current_location"]["lng"], 1.0)


if __name__ == "__main__":
    unittest.main()
