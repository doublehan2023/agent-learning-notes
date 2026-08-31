import unittest

from order_agent.tools import get_order_status

class getOrderStatusTests(unittest.TestCase):
     def test_owner_can_retrieve_order(self):
          result = get_order_status(
               order_id = "123",
               authenticated_customer_id = "customer_1"
          )
          self.assertEqual(result["status"], "success")
          order = result["order"]
          self.assertEqual(order["order_id"], "123")
          self.assertEqual(order["customer_id"], "customer_1")
          self.assertEqual(order["status"], "in_transit")
          self.assertEqual(order["estimated_delivery_date"], "2026-09-03")
          self.assertIsNone(order["carrier_note"])
          self.assertEqual(order["tracking_url"], "https://example.com/track/123")
          
     def test_another_owner_cannot_retrieve_order(self):
          result = get_order_status(
               order_id = "123",
               authenticated_customer_id = "customer_2"
          )
          self.assertEqual(result["status"], "access_denied")
          self.assertNotIn("order", result)
     
     def test_nonexistent_order(self):
          result = get_order_status(
               order_id = "999",
               authenticated_customer_id = "customer_1"
          )
          self.assertEqual(result["status"], "not_found")
          self.assertNotIn("order", result)
     
     def test_delayed_order(self):
          result = get_order_status(
               order_id = "124",
               authenticated_customer_id = "customer_2"
          )
          self.assertEqual(result["status"], "success")
          order = result["order"]
          self.assertEqual(order["order_id"], "124")
          self.assertEqual(order["customer_id"], "customer_2")
          self.assertEqual(order["status"], "delayed")
          self.assertEqual(order["estimated_delivery_date"], "2026-09-05")
          self.assertIsNotNone(order["carrier_note"])
          self.assertEqual(order["tracking_url"], "https://example.com/track/124")
          
     def test_order_response_excludes_unapproved_fields(self):
          result = get_order_status(
               order_id="123",
               authenticated_customer_id="customer_1",
          )

          order = result["order"]

          self.assertNotIn("payment_details", order)
          self.assertNotIn("credit_card_number", order)
          self.assertNotIn("billing_address", order)
          
                    
          
     