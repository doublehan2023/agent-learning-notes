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


def function_call_response(arguments):
    return SimpleNamespace(
        id="response_1",
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


def text_response(text):
    return SimpleNamespace(id="response_2", output=[], output_text=text)


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


if __name__ == "__main__":
    unittest.main()
