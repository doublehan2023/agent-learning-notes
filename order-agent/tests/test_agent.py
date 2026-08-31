import unittest

from order_agent.agent import run_order_agent


class OrderAgentTests(unittest.TestCase):
    def test_refund_request_is_escalated_without_using_an_order(self):
        state = run_order_agent(
            customer_message="I would like a refund for order #123.",
            authenticated_customer_id="customer_1",
        )

        self.assertEqual(state.escalation_reason, "refund_request")
        self.assertIsNone(state.order_id)
        self.assertIsNone(state.tool_result)
        self.assertIn("human review", state.final_response.lower())

    def test_missing_order_id_requests_the_order_id(self):
        state = run_order_agent(
            customer_message="Where is my order?",
            authenticated_customer_id="customer_1",
        )

        self.assertIsNone(state.order_id)
        self.assertIsNone(state.tool_result)
        self.assertIn("provide your order id", state.final_response.lower())

    def test_unknown_order_is_escalated(self):
        state = run_order_agent(
            customer_message="Please check order #999.",
            authenticated_customer_id="customer_1",
        )

        self.assertEqual(state.tool_result["result"], "not_found")
        self.assertEqual(state.escalation_reason, "order_not_found")
        self.assertIn("human review", state.final_response.lower())

    def test_order_owned_by_another_customer_is_escalated(self):
        state = run_order_agent(
            customer_message="Please check order #123.",
            authenticated_customer_id="customer_2",
        )

        self.assertEqual(state.tool_result["result"], "access_denied")
        self.assertEqual(state.escalation_reason, "order_access_denied")
        self.assertIn("human review", state.final_response.lower())

    def test_delayed_order_uses_verified_delivery_information(self):
        state = run_order_agent(
            customer_message="Where is order #124?",
            authenticated_customer_id="customer_2",
        )

        self.assertEqual(state.tool_result["result"], "success")
        self.assertIsNone(state.escalation_reason)
        self.assertIn("delayed", state.final_response.lower())
        self.assertIn("2026-09-05", state.final_response)
        self.assertIn("https://example.com/track/124", state.final_response)

    def test_delivered_order_reported_missing_is_escalated(self):
        state = run_order_agent(
            customer_message="Order #125 is missing even though it says delivered.",
            authenticated_customer_id="customer_3",
        )

        self.assertEqual(state.tool_result["result"], "success")
        self.assertEqual(
            state.escalation_reason,
            "delivered_but_reported_missing",
        )
        self.assertIn("delivered", state.final_response.lower())
        self.assertIn("human review", state.final_response.lower())

    def test_delivered_order_reported_lost_is_escalated(self):
        state = run_order_agent(
            customer_message="Order #125 is marked delivered, but my package is lost.",
            authenticated_customer_id="customer_3",
        )

        self.assertEqual(state.tool_result["result"], "success")
        self.assertEqual(
            state.escalation_reason,
            "delivered_but_reported_missing",
        )
        self.assertIn("human review", state.final_response.lower())

    def test_regular_order_returns_status_and_tracking_link(self):
        state = run_order_agent(
            customer_message="What is the status of order #123?",
            authenticated_customer_id="customer_1",
        )

        self.assertEqual(state.tool_result["result"], "success")
        self.assertIsNone(state.escalation_reason)
        self.assertIn("in transit", state.final_response.lower())
        self.assertIn("2026-09-03", state.final_response)
        self.assertIn("https://example.com/track/123", state.final_response)


if __name__ == "__main__":
    unittest.main()
