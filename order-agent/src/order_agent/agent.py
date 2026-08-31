from .state import AgentState
from .tools import get_order_status
import re

def extract_order_id(message: str) -> str | None:
     match = re.search(r"#(\d+)", message)
     return match.group(1) if match else None

def is_missing_package_report(message: str):
     normalized_message = message.lower()
     return (
          "missing" in normalized_message
          or "not received" in normalized_message
     )

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
     
     state.order_id = extract_order_id(customer_message)
     
     if state.order_id is None:
          state.final_response = "Please provide your order ID so I can check its status."
          return state
     
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
     
     

