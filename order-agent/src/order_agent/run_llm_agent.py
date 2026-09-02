from .llm_agent import run_llm_order_agent

CASES = [
    {
        "name": "No order ID",
        "customer_message": "Where is my package?",
        "authenticated_customer_id": "customer_2",
    },
    {
        "name": "Unauthorized order access",
        "customer_message": "Where is order #124?",
        "authenticated_customer_id": "customer_1",
    },
    {
        "name": "Delivered but missing",
        "customer_message": "Order #125 says delivered, but I did not receive it.",
        "authenticated_customer_id": "customer_3",
    },
    {
        "name": "Refund request",
        "customer_message": "I want a refund for order #123.",
        "authenticated_customer_id": "customer_1",
    },
]

for case in CASES:
    print(f"\n--- {case['name']} ---")
    state = run_llm_order_agent(
        customer_message=case["customer_message"],
        authenticated_customer_id=case["authenticated_customer_id"],
    )
    print(state)
