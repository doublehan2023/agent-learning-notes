import unittest
from types import SimpleNamespace
from unittest.mock import patch

from order_agent import llm_agent


class FakeResponses:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.responses = FakeResponses(responses)


def function_call_response(arguments, response_id="response_1"):
    return SimpleNamespace(
        id=response_id,
        output=[
            SimpleNamespace(
                type="function_call",
                name="get_order_status",
                arguments=arguments,
                call_id="call_1",
            )
        ],
        output_text="",
    )


def text_response(text, response_id="response_2"):
    return SimpleNamespace(id=response_id, output=[], output_text=text)


class LlmOrderAgentTests(unittest.TestCase):
    def run_with_fake_client(self, responses, **kwargs):
        fake_client = FakeClient(responses)
        with patch.object(llm_agent, "client", fake_client):
            state = llm_agent.run_llm_order_agent(**kwargs)
        return state, fake_client

    def test_tool_call_uses_authenticated_customer_and_returns_final_response(self):
        state, fake_client = self.run_with_fake_client(
            [
                function_call_response('{"order_id": "124"}'),
                text_response("Your order is delayed and is expected on September 5."),
            ],
            customer_message="Where is order #124?",
            authenticated_customer_id="customer_2",
        )

        self.assertEqual(state.order_id, "124")
        self.assertEqual(state.tool_result["result"], "success")
        self.assertEqual(state.final_response, "Your order is delayed and is expected on September 5.")
        self.assertEqual(len(fake_client.responses.calls), 2)
        self.assertEqual(
            fake_client.responses.calls[1]["input"][0]["call_id"],
            "call_1",
        )

    def test_unauthorized_customer_receives_only_access_denied_tool_result(self):
        state, fake_client = self.run_with_fake_client(
            [
                function_call_response('{"order_id": "124"}'),
                text_response("I cannot confirm that order. A human reviewer will assist."),
            ],
            customer_message="Where is order #124?",
            authenticated_customer_id="customer_1",
        )

        self.assertEqual(state.tool_result["result"], "access_denied")
        self.assertNotIn("order", state.tool_result)
        self.assertEqual(len(fake_client.responses.calls), 2)

    def test_malformed_tool_arguments_are_escalated_without_second_model_call(self):
        state, fake_client = self.run_with_fake_client(
            [function_call_response("not valid JSON")],
            customer_message="Where is order #124?",
            authenticated_customer_id="customer_2",
        )

        self.assertEqual(
            state.escalation_reason,
            "Order ID could not be read from the tool request.",
        )
        self.assertIn("human reviewer", state.final_response.lower())
        self.assertEqual(len(fake_client.responses.calls), 1)

    def test_follow_up_message_uses_previous_response_id(self):
        fake_client = FakeClient(
            [
                text_response("Please provide your order ID.", "response_1"),
                function_call_response('{"order_id": "124"}', "response_2"),
                text_response(
                    "Your order is delayed and is expected on September 5.",
                    "response_3",
                ),
            ]
        )

        with patch.object(llm_agent, "client", fake_client):
            first_state = llm_agent.run_llm_order_agent(
                customer_message="Where is my package?",
                authenticated_customer_id="customer_2",
            )
            second_state = llm_agent.run_llm_order_agent(
                customer_message="It is #124.",
                authenticated_customer_id="customer_2",
                previous_response_id=first_state.response_id,
            )

        self.assertEqual(first_state.response_id, "response_1")
        self.assertEqual(second_state.order_id, "124")
        self.assertEqual(second_state.tool_result["result"], "success")
        self.assertEqual(second_state.response_id, "response_3")
        self.assertEqual(
            fake_client.responses.calls[1]["previous_response_id"],
            first_state.response_id,
        )
        self.assertEqual(len(fake_client.responses.calls), 3)

    def test_no_order_id_returns_text_without_tool_call(self):
        state, fake_client = self.run_with_fake_client(
            [text_response("Please provide your order ID.", "response_1")],
            customer_message="Where is my package?",
            authenticated_customer_id="customer_2",
        )

        self.assertIsNone(state.order_id)
        self.assertIsNone(state.tool_result)
        self.assertEqual(state.response_id, "response_1")
        self.assertIn("order ID", state.final_response)
        self.assertEqual(len(fake_client.responses.calls), 1)

    def test_refund_request_is_escalated_without_a_tool_call(self):
        state, fake_client = self.run_with_fake_client(
            [
                text_response(
                    "I can't process refunds. A human reviewer will assist.",
                    "response_1",
                )
            ],
            customer_message="I want a refund for order #123.",
            authenticated_customer_id="customer_1",
        )

        self.assertIsNone(state.tool_result)
        self.assertIn("human reviewer", state.final_response.lower())
        self.assertNotIn("refund approved", state.final_response.lower())
        self.assertEqual(len(fake_client.responses.calls), 1)

    def test_delivered_but_missing_order_is_escalated(self):
        state, fake_client = self.run_with_fake_client(
            [
                function_call_response('{"order_id": "125"}', "response_1"),
                text_response(
                    "The order is marked delivered. "
                    "Since you did not receive it, a human reviewer will assist.",
                    "response_2",
                ),
            ],
            customer_message="Order #125 says delivered, but I did not receive it.",
            authenticated_customer_id="customer_3",
        )

        self.assertEqual(state.tool_result["result"], "success")
        self.assertEqual(state.tool_result["order"]["status"], "delivered")
        self.assertIn("marked delivered", state.final_response.lower())
        self.assertIn("human reviewer", state.final_response.lower())
        self.assertEqual(len(fake_client.responses.calls), 2)


if __name__ == "__main__":
    unittest.main()
