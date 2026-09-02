# LLM Tool Loop for the Order Agent

**Date:** 2026-09-01  
**Focus:** Add an LLM layer that can choose the safe order-status tool while keeping authorization and order data under application control.

## What was built

The project now has an LLM-powered runner in `src/order_agent/llm_agent.py` and a small manual runner in `src/order_agent/run_llm_agent.py`.

The LLM version reuses the existing safe components:

- `ORDER_STATUS_AGENT_INSTRUCTIONS` for the role, evidence rules, and escalation policy.
- `get_order_status` as the only available business-data tool.
- Backend authorization through `authenticated_customer_id`.
- `AgentState` to record the request, evidence, escalation reason, and final response.

The deterministic `agent.py` remains available. It is useful as a simple baseline and as a way to test the core policy without a live model call.

## Tool contract and trust boundary

The model sees a narrow tool contract:

```text
get_order_status(order_id)
```

It does **not** receive a customer ID or direct access to `ORDERS`.

When the model requests an order lookup, the Python application adds the trusted authenticated identity before calling the existing backend:

```text
model requests order_id
  -> application supplies authenticated_customer_id
  -> get_order_status verifies ownership and filters fields
  -> model receives only the safe result
```

This is the key safety pattern: an LLM may choose whether to request information, but it does not decide whether it is authorized to see that information.

## LLM tool loop

The new agent follows this loop:

1. Send the customer message, agent instructions, and the one tool definition to the model.
2. If the model returns a normal text response, return it as the final response.
3. If it returns `get_order_status`, parse the requested `order_id`.
4. Call the existing backend tool with the authenticated customer ID.
5. Send the filtered tool result back to the model as a function-call output.
6. Ask the model to produce the customer-facing final response without further tool use.

If tool-call arguments are malformed, the agent avoids a second model call and escalates safely.

## Tests added and verified

Three no-network tests were added for the LLM integration using a fake client:

1. A valid tool call retrieves the order using the authenticated customer identity and returns the model's final response.
2. An unauthorized lookup receives only the `access_denied` result, not another customer's order data.
3. Malformed model tool arguments produce a safe escalation without a second model call.

The full suite has **16 passing tests**: 8 deterministic-agent tests, 5 backend-tool tests, and 3 LLM-loop tests.

Run it with:

```bash
cd /Users/hanwang/Learn/agent-learning-notes/order-agent
PYTHONPATH="$(pwd)/src" python3 -m unittest discover -s tests -v
```

## What this demonstrates

- An LLM can replace narrow regex and keyword understanding without replacing trusted business logic.
- Function calling is an application-controlled loop: the model requests a tool, and the application validates and executes it.
- Mocked model responses make the integration testable without API access, cost, or model-output variability.
- The final customer response is generated only after the model receives verified evidence from the tool.

## Next improvements

1. Return and persist the response ID so a customer can provide an order ID in a later turn without repeating the earlier question.
2. Choose one model configuration for both requests in the loop, rather than using different models for the initial and final response.
3. Add tests for a no-order-ID text response, refund escalation language, and delivered-but-missing escalation language from the LLM path.
4. After these local tests are stable, run a few manual live cases with an API key kept outside the repository.
