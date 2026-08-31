from mock_data import ORDERS

APPROVED_ORDER_FIELDS = (
     "order_id",
     "status",
     "estimated_delivery_date",
     "carrier_note",
     "tracking_url",
)

def get_order_status(order_id: str, authenticated_customer_id: str,) -> dict:
     order = ORDERS.get(order_id)
     
     if order is None:
          return {
               "result": "not_found",
               "message": "No order was found for the provided order ID."
          }
     if order["customer_id"] != authenticated_customer_id:
          return {
               "result": "access_denied",
               "message": "The order cannot be accessed by this customer."
          }
     safe_order = {
          field: order[field]
          for field in APPROVED_ORDER_FIELDS
          if field in order
     }
     
     return {
          "result": "success",
          "order": safe_order,
     }