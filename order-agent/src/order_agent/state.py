from dataclasses import dataclass
from typing import Any

@dataclass
class AgentState:
     authenticated_customer_id: str
     customer_message: str
     
     order_id: str | None = None
     tool_result: dict[str, Any] | None = None
     
     escalation_reason: str | None = None
     final_response: str | None = None