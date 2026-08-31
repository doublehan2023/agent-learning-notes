# Order-Agent Tool Foundation

**Date:** 2026-08-30  
**Focus:** Build and test the safe data-tool layer for the order-status agent.

## What was built

Created the first runnable layer of the order-status agent in [`order-agent/`](../order-agent/):

```text
order-agent/
├── README.md
├── src/
│   └── order_agent/
│       ├── __init__.py
│       ├── mock_data.py
│       └── tools.py
└── tests/
    └── test_tools.py
```

This first layer uses only Python standard-library code and mock data. It does not use an API key or an LLM yet.

## Mock order data

The mock order data contains orders for these situations:

- Normal in-transit shipment
- Carrier-reported delayed shipment
- Delivered shipment
- Nonexistent order lookup
- Unauthorized customer attempting to access another customer’s order

Each order includes:

```text
order_id
customer_id
status
estimated_delivery_date
carrier_note
tracking_url
```

## The safe lookup tool

The tool contract is:

```text
get_order_status(order_id, authenticated_customer_id)
```

It follows this safety sequence:

```text
Find order → does it exist?
          → does the authenticated customer own it?
          → return only approved fields
```

Possible outcomes:

| Result | Meaning |
| --- | --- |
| `success` | The authenticated customer owns the order; approved details are returned. |
| `not_found` | No order matches the requested ID. |
| `access_denied` | The order does not belong to the authenticated customer. |

The approved output fields are:

```text
order_id
status
estimated_delivery_date
carrier_note
tracking_url
```

`customer_id` is deliberately not returned. This reinforces an important principle: the backend/tool enforces data access, rather than relying on the agent prompt to do so.

## Fixes applied

- Changed the mock orders container to a dictionary so lookups by order ID work.
- Changed the tool import to a package-relative import: `from .mock_data import ORDERS`.
- Renamed `_init_.py` to `__init__.py` so Python recognizes the package conventionally.
- Aligned tests with the tool’s `result` outcome field.
- Removed test expectations that would expose unapproved `customer_id` data.
- Added an assertion that `customer_id` is absent from a successful tool response.

## Tests

Five tests pass:

1. The owner can retrieve their order.
2. Another customer cannot access that order.
3. A nonexistent order returns `not_found`.
4. A delayed order returns its delay information.
5. Unapproved fields are excluded from the response.

Run the tests from the `order-agent` directory:

```bash
cd /Users/hanwang/Learn/agent-learning-notes/order-agent
PYTHONPATH="$(pwd)/src" python3 -m unittest discover -s tests -v
```

The explicit `cd` and absolute `PYTHONPATH` avoid test-discovery issues caused by running the command from the repository root.

## Takeaways

1. Build the trusted tool layer before adding an LLM.
2. A tool should verify ownership before returning any order details.
3. Return only the fields the agent actually needs.
4. Test normal, missing-data, unauthorized, and delayed-shipment paths.
5. The agent will later use tool output as evidence; it should not decide authorization itself.

## Next step

Add the agent’s version-2 instructions and a small decision loop on top of `get_order_status`.
