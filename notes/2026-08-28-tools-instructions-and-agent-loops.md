# Tools, Instructions, and Agent Loops

**Date:** 2026-08-28  
**Focus:** How agents use tools, how instructions guide behavior, and how an agent completes multi-step work safely.

## Agent tools

Tools let an agent retrieve information or take actions in external systems.

```text
User goal → agent decides → tool call → tool result → agent decides again → result
```

Example: a customer asks, “Where is my order?”

1. The agent determines it needs order data.
2. It calls `get_order_status(order_id)`.
3. The tool returns the status.
4. The agent responds with the update, or asks for missing information.

The agent chooses a named tool and supplies arguments. The application executes the real operation, returns the result, and the agent decides what to do next.

## Tool types

| Type | Purpose | Examples |
| --- | --- | --- |
| Data tools | Retrieve context or information | Search the web, read a PDF, query orders |
| Action tools | Change an external system | Send an email, create a ticket, issue a refund |
| Orchestration tools | Delegate work | Call a research or translation sub-agent |

## Designing good tools

A good tool has:

- A clear name, such as `get_order_status` instead of `lookup`.
- A precise description of when to use it.
- Explicit required inputs.
- Predictable outputs.
- Clear error behavior and side effects.

Example tool contract:

```text
Tool: get_order_status
Input: order_id
Output: order status, estimated delivery date, and tracking link
Restriction: return only the authenticated customer’s own order
```

## Tool safety and permissions

Start with the smallest, least-powerful set of tools that can accomplish the job.

For customer support, `get_order_status` is a good first tool because it is read-only and lower risk than `send_email` or `issue_refund`.

The tool should receive the authenticated customer identity from the signed-in session—not trust a value supplied by the agent or user. The backend must verify that the requested order belongs to that customer.

```text
Request → authenticated identity → verify order ownership → return limited status
```

If ownership cannot be verified, return a safe error without revealing whether the order exists.

Key principle: an agent can request a tool call, but the tool and backend must enforce permissions and business rules.

## Agent instructions

Instructions are an agent’s operating manual. They tell the agent what it is responsible for, how it uses tools, what it must not do, and when it should stop or escalate.

A useful instruction set defines:

1. **Role** — what the agent is.
2. **Goal** — the outcome it should achieve.
3. **Context** — relevant policies and facts.
4. **Tool policy** — which tools to use and when.
5. **Boundaries** — prohibited actions.
6. **Escalation and stopping rules** — when to ask a person or finish.
7. **Output style** — what a good answer looks like.

Example:

```text
Role: You are a customer-support agent for an online store.

Goal: Resolve straightforward order-status questions accurately and politely.

Tool policy: Use get_order_status only after you have an order ID.
If the user does not provide one, ask for it.

Boundaries: Do not access an order unless the backend verifies that it belongs
to the authenticated customer. Do not issue refunds or modify orders.

Escalation: Escalate billing disputes, security concerns, legal threats, and
delivery claims that cannot be resolved with order-status data.
```

Good instructions are specific but not bloated. They should define outcomes, constraints, approvals, and success criteria. Tool-specific details generally belong in the tool description.

Source: [OpenAI Docs: Model guidance](https://developers.openai.com/api/docs/guides/latest-model)

## Missing evidence rule

When a tool returns no result, the agent should not invent an answer.

```text
If get_order_status returns no result, do not guess or invent an order status.
Tell the customer that you could not locate an order using the provided details.
Ask them to verify the order number or provide the email used for the purchase.
```

This pattern is useful generally: state what is known, do not guess, and give the user a safe next step.

## The agent loop

An agent runs a loop rather than producing a single response.

```text
1. Read the goal and current context.
2. Decide: answer, ask a question, or call a tool.
3. Inspect the tool result.
4. Decide what comes next.
5. Repeat until a stopping condition is met.
```

Order-status example:

```text
User asks where an order is.
→ No order ID: ask for it.
→ Order ID received: call get_order_status.
→ Status found: provide the status and delivery estimate.
→ Stop.
```

## Stopping conditions

An agent should stop when:

- The user’s request is answered with enough evidence.
- Required information is missing, so it needs to ask the smallest necessary question.
- A human must approve the next action.
- The case needs escalation.
- It reaches a configured tool-call or retry limit.

Example rule:

```text
After receiving order-status information, answer the customer and stop.
Do not call more tools unless the result is missing, contradictory,
or the customer asks for another action.
```

## Handling a tool failure

If the order database is temporarily unavailable:

```text
If get_order_status has a temporary failure, retry once.
If it still fails, tell the customer that order information is temporarily
unavailable, do not guess the status, and escalate the case to a human.
```

Retrying this data tool is safe because it is read-only. Retrying action tools requires more care: repeating `issue_refund`, for example, could accidentally create duplicate refunds.

## Takeaways

1. Tools allow agents to retrieve information and act outside the model.
2. Tool/backend code—not the agent alone—must enforce permissions and safety rules.
3. Instructions define the agent’s role, goals, boundaries, and escalation behavior.
4. Agents should say when evidence is missing instead of guessing.
5. The agent loop needs explicit stopping conditions and error handling.
6. Retries are safer for read-only tools than for tools with external side effects.

## Next topic

- Memory and state: how an agent keeps the right context across steps and conversations.
