from .state import AgentState
from .tools import get_order_status
import re

def extract_order_ids(message: str) -> list[str]:
     matches = re.findall(
          r"#(\d+)|\b(?:order|package)\s*(?:number\s*)?(\d+)\b",
          message,
          flags=re.IGNORECASE,
     )
     order_ids = [number for match in matches for number in match if number]
     return list(dict.fromkeys(order_ids))


def extract_order_id(message: str) -> str | None:
     order_ids = extract_order_ids(message)
     return order_ids[0] if order_ids else None

def is_missing_package_report(message: str):
     normalized_message = message.lower()

     missing_phrases = [
          "missing",
          "lost",
          "not received",
          "never arrived",
          "nothing at my door",
          "can't find my package",
          "not here",
     ]
     return any(phrase in normalized_message for phrase in missing_phrases)

def run_order_agent(
     customer_message: str,
     authenticated_customer_id: str,
)-> AgentState:
     state = AgentState(
          customer_message=customer_message,
          authenticated_customer_id=authenticated_customer_id
     )
     
     if "refund" in customer_message.lower():
          state.escalation_reason = "refund_request"
          state.final_response = (
               "I can help escalate your refund request for human review."
          )
          return state
     
     order_ids = extract_order_ids(customer_message)

     if not order_ids:
          state.final_response = "Please provide your order ID so I can check its status."
          return state

     if len(order_ids) > 1:
          state.final_response = (
               "I found multiple order IDs. Which order would you like me to check?"
          )
          return state

     state.order_id = order_ids[0]
     
     state.tool_result = get_order_status(
          order_id=state.order_id,
          authenticated_customer_id=authenticated_customer_id,
     )
     
     result = state.tool_result["result"]
     
     if result == "not_found":
          state.escalation_reason = "order_not_found"
          state.final_response = (
               "I couldn't locate an order with that ID, so I've escalated the case "
               "for human review."
          )
          return state

     if result == "access_denied":
          state.escalation_reason = "order_access_denied"
          state.final_response = (
               "I can't confirm access to that order, so I've escalated the case "
               "for human review."
          )
          return state
     
     order = state.tool_result["order"]
     if order["status"] == "delayed":
          delivery_date = order["estimated_delivery_date"]
          carrier_note = order["carrier_note"]

          state.final_response = (
               f"Your shipment is delayed. The updated delivery estimate is "
               f"{delivery_date}. "
               f"Carrier update: {carrier_note}. "
               f"You can check the latest details here: {order['tracking_url']}"
          )
          return state
     
     if (order["status"] == "delivered" and is_missing_package_report(customer_message)):
          state.escalation_reason = "delivered_but_reported_missing"
          state.final_response = (
               "Your order is recorded as delivered, but I understand you reported "
               "it missing. I've escalated this case for human review."
          )
          return state
     
     friendly_status = order["status"].replace("_", " ")

     state.final_response = (
          f"Your order is currently {friendly_status}. "
          f"The estimated delivery date is {order['estimated_delivery_date']}. "
          f"You can check tracking details here: {order['tracking_url']}"
     )
     return state
     
     
