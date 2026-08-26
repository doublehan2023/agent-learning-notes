# Agents, Deterministic Workflows, and Guardrails

**Date:** 2026-08-26  
**Focus:** When to use an AI agent, when to use a deterministic workflow, and how guardrails enable safe autonomy.

## Agent or deterministic workflow?

A **deterministic workflow** follows predefined rules and steps.

```text
Input → fixed rules → fixed sequence → output
```

Example: send a reminder email exactly three days before every scheduled meeting.

```text
Meeting scheduled → wait until 3 days before → send reminder email
```

This task does not need an agent because the trigger, timing, and action are explicit. An agent would add unnecessary cost and unpredictability.

An **agent** is better when the workflow cannot be fully specified in advance.

```text
Goal → reason about context → choose actions → inspect results → adapt
```

## When agents are useful

Consider an agent when work involves:

- **Ambiguous or unstructured information**, such as emails, PDFs, and conversations.
- **Contextual judgment**, exceptions, or nuanced decisions.
- **Complex rules** that would be expensive or brittle to encode and maintain manually.
- **Multi-step tasks** where each next action depends on the previous result.

Do not use an agent merely because AI is available. A fixed, predictable, high-volume, or safety-critical rule is often better handled by conventional software.

## Example: customer-support email handling

Task: read incoming support emails, determine the customer’s need, retrieve relevant account information, and decide whether to resolve, ask for details, or escalate.

This is a good agent use case because:

1. Understanding what a customer means requires contextual reasoning.
2. The account information needed differs by case.
3. The correct next action depends on the email, account context, and policy.
4. It would be difficult to write complete deterministic rules for every possible exception.

## Best design: combine agents and deterministic systems

An effective system often uses both approaches.

```text
Incoming email
  → agent classifies and investigates
  → deterministic systems fetch account/order data
  → agent recommends: resolve / ask / escalate
  → human approval for high-risk cases
  → deterministic system sends the approved action
```

The agent handles flexible reasoning. Deterministic systems handle reliable operations, such as retrieving records and sending an approved message.

## Human in the loop

**Human-in-the-loop** means a person reviews or approves actions that are risky, costly, sensitive, or hard to reverse.

For customer support, the agent might:

- Auto-resolve low-risk, clearly policy-compliant issues.
- Request more information if necessary details are missing.
- Require approval for refunds over a threshold.
- Escalate legal, safety, account-security, or uncertain cases.

Human approval does not need to apply to every action. The level of oversight should match the risk.

## Guardrails

Guardrails are boundaries that keep an agent safe and predictable. They define the agent’s safe operating area rather than simply blocking it.

Guardrails can limit:

- Accepted inputs
- Accessible data
- Available tools
- Allowed actions
- Outputs
- Actions requiring human approval

### Guardrail 1: least-privilege data access

The agent should access only data needed for the current customer case. It should not have broad access to the entire customer database.

Example rule:

> The agent may retrieve approved fields for the identified customer—such as order status, subscription plan, and recent support history—but may not access passwords, full payment details, or other customers’ data.

### Guardrail 2: risk-based email sending

The agent should classify the case’s risk before sending an email.

| Case type | Send automatically? |
| --- | --- |
| Order-status update | Yes |
| Request for a missing order number | Yes |
| Billing dispute | No — draft for review |
| Refund approval | No — require approval |
| Legal, safety, or account-security issue | No — escalate immediately |

The agent may prepare drafts for high-risk cases, but a person must approve the final message.

## Takeaways

1. Use deterministic workflows for fixed, predictable rules.
2. Use agents when context, judgment, and next steps vary.
3. Combining agents with deterministic systems is usually the practical design.
4. Apply human approval to high-risk or irreversible decisions.
5. Guardrails create safe lanes for autonomy by restricting data access, tools, and actions.

## Next topics

- Tools: how agents retrieve information and take actions
- Instructions: how to tell an agent what good work looks like
- Building a small first agent project
