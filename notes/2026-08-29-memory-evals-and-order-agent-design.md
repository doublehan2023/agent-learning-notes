# Memory, Evals, and Order-Agent Design

**Date:** 2026-08-29  
**Focus:** Agent memory and state, evaluations, and a version-2 design for a safe order-status support agent.

## Memory and state

An agent needs context to make decisions, but “memory” is not one thing.

| Type | Purpose | Example |
| --- | --- | --- |
| Working memory / conversation state | Supports the current workflow | Current goal, order ID, tool results |
| Long-term memory | Retains useful information across conversations | Preferred language or contact channel |
| System of record | Holds authoritative business data | Live order status, account status, refund history |

The key rule is:

> Remember preferences; verify facts that can change or control access.

For a customer-support agent:

- Retrieve durable preferences, such as language and contact channel, from a trusted profile store.
- Re-check authentication and authorization for every session.
- Query the live database for order status, delivery information, account standing, and refund eligibility.

Do not treat agent memory as the source of truth for sensitive or changing facts.

## Agent evaluations

An **evaluation** (eval) is a repeatable test suite that checks whether an agent behaves correctly and safely.

An eval can test:

- Tool selection and arguments
- Accuracy and evidence use
- Escalation behavior
- Safety and privacy boundaries
- Regression after changing a prompt, model, or tool

The evaluation workflow:

```text
Define success → collect realistic cases → run agent → grade results
→ inspect failures → make one change → rerun the same evals
```

Each eval case should include:

```text
Case name:
Customer message:
Mock tool result:
Expected tool behavior:
Expected final response:
Forbidden behavior:
```

Source: [OpenAI API reference: Evals](https://developers.openai.com/api/reference/java/resources/evals/methods/create)

## Version-2 order-status support agent

### Role

You are a customer order-status support agent.

### Goal

Help authenticated customers understand their current order status, including delayed-shipment updates, using live verified order information.

### Tool rule

Use `get_order_status` when an order ID is available. If no order ID is available, ask the customer for it.

### Evidence rule

If order information is unavailable, incomplete, or contradictory, do not invent an order status. Explain that the information cannot currently be confirmed and escalate the case for human review.

### Delayed-shipment definition

A shipment is delayed when either:

- The carrier reports a delay, or
- The current customer-local date is later than the estimated delivery date and the order is not marked `delivered`.

### Escalation rules

Escalate when:

- The customer requests a refund.
- The customer reports that a package is lost.
- The order is marked `delivered`, but the customer reports it was not received.
- The agent cannot verify that the order belongs to the authenticated customer.

### Success criteria

The agent provides the verified current status and, when available, the delivery estimate or delay explanation plus a clear next step. It does not make unsupported claims or perform actions outside its authority.

## Expected-response specifications

Use this four-part pattern when defining an agent response:

```text
Trigger: What situation caused this response?
Evidence: What tool result supports it?
Must include: What facts and next step are required?
Must not say/do: What would be unsafe or misleading?
```

### Carrier-reported delay

```text
Trigger: The carrier reports a delay.
Evidence: Verified order status and updated delivery estimate.
Must include: The confirmed delay, updated delivery estimate, and a clear next
step, such as using the tracking link or checking back after the new date.
Must not: Invent a reason for the delay, promise compensation, or claim the
package is lost.
```

If the carrier reports a delay but gives no updated estimate, the agent should say that no new date is available rather than guessing one.

### Marked delivered but customer reports it missing

```text
Trigger: The customer reports an order is missing but it is marked “delivered.”
Evidence: Verified order status.
Must include: State that the order is recorded as delivered, acknowledge the
customer reports it missing, and explain that the case has been escalated for
human review.
Must not: Claim the customer received the package, invent an explanation,
promise compensation or a replacement, or dismiss the report.
```

## Planned prototype

The prototype will be built in two stages:

1. Build a self-contained Python prototype using mock order data—no API key required.
2. Optionally replace the mock response layer with a real LLM using a custom `get_order_status` function.

Implementation stages:

1. Create a small project structure for instructions, mock data, the tool, and eval cases.
2. Implement mock order data for on-time, delayed, delivered, unavailable, and unauthorized orders.
3. Encode the version-2 instructions and guardrails.
4. Implement the agent loop: collect order ID, query tool, handle errors, respond, or escalate.
5. Add and run eval cases.
6. Inspect results and make one change at a time.

The Responses API supports the model-plus-custom-tool pattern used by a later LLM-backed version. [OpenAI API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)

## Next step

Create the prototype structure and mock order data.
