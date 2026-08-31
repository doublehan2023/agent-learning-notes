# Order-Agent Decision Loop

**Date:** 2026-08-31  
**Focus:** Add a decision layer to the safe order lookup tool and test the agent’s behavior end to end.

## What was built

The order-agent project now contains a mock, deterministic agent loop on top of the safe `get_order_status` tool.

New project components:

```text
src/order_agent/
├── instructions.py  # Version-2 agent specification
├── state.py         # AgentState data structure
└── agent.py         # Decision loop
```

This version does not use an LLM yet. It uses simple rules so the decision flow, tool use, boundaries, and test cases are easy to inspect.

## Agent instructions

The agent instructions include:

- Role: customer order-status support agent.
- Goal: help authenticated customers understand live, verified order status, including delays.
- Tool rule: use `get_order_status` only when an order ID is available.
- Evidence rule: do not invent a status when data is missing, incomplete, or contradictory.
- Delay definition: carrier-reported delay or a passed estimate for an undelivered order.
- Escalation rules: refunds, lost packages, delivered-but-missing reports, and unauthorized access.
- Success criteria and stopping rules.

## Agent state

The `AgentState` object records the essential working state of a run:

```text
authenticated_customer_id
customer_message
order_id
tool_result
escalation_reason
final_response
```

This is short-term task state. It lets the system keep track of evidence retrieved, whether an escalation occurred, and the final response without treating the model as a source of truth.

## Decision loop

The mock agent follows this flow:

```text
Refund request?
  → Escalate without calling an order or refund tool.

No order ID?
  → Ask the customer to provide it.

Order ID available?
  → Call get_order_status.

not_found or access_denied?
  → Explain safely and escalate.

Delayed order?
  → State the verified delay, delivery estimate, carrier update, and tracking link.

Delivered order reported missing or lost?
  → Acknowledge the order is recorded as delivered and escalate.

Otherwise
  → State the verified current status, estimate, and tracking link, then stop.
```

The agent calls the data tool before deciding how to respond to an order-specific request. It does not use a tool for a refund request because refunds are out of scope and require human review.

## Natural-language detection in the mock version

The prototype extracts an order ID from a pattern such as `#123` and uses simple keyword matching for specific reports:

- `refund` → refund escalation
- `missing`, `lost`, or `not received` → possible missing-package report

This is intentionally limited. It demonstrates the decision architecture, but an LLM could later handle more varied language while keeping the same tool and safety boundaries.

## Tests added and verified

The full suite now has 13 passing tests.

Agent-level cases cover:

1. Refund request escalates without an order-tool call.
2. Missing order ID prompts the customer for one.
3. Unknown order escalates safely.
4. Unauthorized order access escalates safely.
5. Carrier-reported delay uses verified estimate and tracking information.
6. Delivered order reported missing escalates.
7. Delivered order reported lost escalates.
8. Normal in-transit order returns status and tracking information.

The lost-package regression test was added because the specification required lost-package escalation but the first keyword rule only recognized `missing` and `not received`.

Run the complete suite:

```bash
cd /Users/hanwang/Learn/agent-learning-notes/order-agent
PYTHONPATH="$(pwd)/src" python3 -m unittest discover -s tests -v
```

## Takeaways

1. Separate trusted tool behavior from agent decision behavior.
2. Record task state explicitly: identifiers, tool results, escalation reason, and response.
3. Define a clear stopping point after a verified answer or escalation.
4. Every specification rule should have a matching test; the lost-package test caught an implementation gap.
5. Keyword rules are useful for learning the architecture, but they are not robust natural-language understanding.

## Next topic

Explore how an LLM can replace narrow keyword rules while preserving the existing tool permissions, guardrails, state, and eval cases.
