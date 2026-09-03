import json
from typing import Any

try:
     from openai import OpenAI
except ImportError:
     OpenAI = None

from .instructions import ORDER_STATUS_AGENT_INSTRUCTIONS
from .state import AgentState
from .tools import get_order_status

client: Any | None = None


def _get_client() -> Any:
     """Create the API client only when a live model call is needed."""
     global client
     if client is None:
          if OpenAI is None:
               raise RuntimeError(
                    "The OpenAI SDK is required for live runs. Install it with: pip install openai"
               )
          client = OpenAI()
     return client

ORDER_STATUS_TOOL = {
     "type": "function",
     "name": "get_order_status",
     "description": (
          "Retrieve verified current status information for a customer's order. "
          "Use this only when the customer provides an order ID and asks about "
          "its current status."
     ),
     "parameters": {
          "type": "object",
          "properties": {
               "order_id": {
                    "type": "string",
                    "description": (
                         "The unique identifier for the customer's order. "
                         "This ID is typically provided by the customer in their message."
                    ),
               },
          },
          "required": ["order_id"],
          "additionalProperties": False,
     },
     "strict": True,
}

MODEL = "gpt-5.5"

def run_llm_order_agent(
     customer_message: str,
     authenticated_customer_id: str,
     previous_response_id: str | None = None,
) -> AgentState:
     request = {
          "model": MODEL,
          "instructions": ORDER_STATUS_AGENT_INSTRUCTIONS,
          "input": customer_message,
          "tools": [ORDER_STATUS_TOOL],
     }
     if previous_response_id is not None:
          request["previous_response_id"] = previous_response_id

     active_client = _get_client()
     response = active_client.responses.create(**request)
     
     function_calls = [
          item for item in response.output
          if item.type == "function_call"
     ]
     
     if not function_calls:
          return AgentState(
               authenticated_customer_id=authenticated_customer_id,
               customer_message=customer_message,
               final_response=response.output_text,
               response_id=response.id,
          )

     function_call = function_calls[0]

     if function_call.name != "get_order_status":
          return AgentState(
               authenticated_customer_id=authenticated_customer_id,
               customer_message=customer_message,
               escalation_reason="Unsupported tool request.",
               final_response=(
                    "I'm unable to complete that request. "
                    "A human reviewer will assist."
               ),
               response_id=response.id,
          )

     try:
          arguments = json.loads(function_call.arguments)
          order_id = arguments["order_id"]
     except (json.JSONDecodeError, KeyError, TypeError):
          return AgentState(
               authenticated_customer_id=authenticated_customer_id,
               customer_message=customer_message,
               escalation_reason="Order ID could not be read from the tool request.",
               final_response=(
                    "I couldn’t confirm the order information. "
                    "A human reviewer will assist."
               ),
               response_id=response.id,
          )

     tool_result = get_order_status(
          order_id=order_id,
          authenticated_customer_id=authenticated_customer_id,
     )

     final_response = active_client.responses.create(
          model=MODEL,
          instructions=ORDER_STATUS_AGENT_INSTRUCTIONS,
          previous_response_id=response.id,
          input=[
               {
                    "type": "function_call_output",
                    "call_id": function_call.call_id,
                    "output": json.dumps(tool_result),
               }
          ],
          tool_choice="none",
     )

     return AgentState(
          authenticated_customer_id=authenticated_customer_id,
          customer_message=customer_message,
          order_id=order_id,
          tool_result=tool_result,
          final_response=final_response.output_text,
          response_id=final_response.id
     )
