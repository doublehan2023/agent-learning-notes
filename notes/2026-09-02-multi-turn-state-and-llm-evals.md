# Multi-Turn State and LLM Evaluations

**Date:** 2026-09-02  
**Focus:** Continue a customer conversation safely across turns and expand evaluation coverage for the LLM tool loop.

## What was built

The LLM order agent can now receive an optional `previous_response_id` and returns a `response_id` in `AgentState`.

```text
Turn 1: “Where is my package?”
  -> Agent asks for an order ID.
  -> Save response_id.

Turn 2: “It is #124.”
  -> Send the new message with previous_response_id.
  -> Model sees the earlier conversation, requests the safe lookup,
     and receives verified order data.
```

`previous_response_id` links the next model request to the earlier response. The application still supplies the customer identity separately for every tool execution. Conversation context must never be treated as proof that a customer is authorized to access an order.

## Consistent model configuration

The runner now stores its model choice in one `MODEL` constant and uses it for both stages of a tool loop:

1. Interpret the customer message and decide whether to call the tool.
2. Turn the verified tool result into the final response.

Keeping this configuration in one place makes the behavior easier to inspect, change, and test.

## State versus model context

Two kinds of state now have different jobs:

| State | Purpose | Trusted for authorization? |
| --- | --- | --- |
| `AgentState` | Local record of a run: message, order ID, tool result, escalation, final response, and response ID. | Only the server-provided customer ID is trusted. |
| `previous_response_id` | Lets the model continue the immediate customer conversation. | No. It provides context, not permission. |

The Responses API supports `previous_response_id` for multi-turn conversations. When using it, send the agent instructions again on each request because instructions from the earlier response are not automatically carried forward. [OpenAI Docs](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)

## LLM-path tests added

The fake-client evaluation suite now covers:

1. A normal authorized lookup and final response.
2. An unauthorized lookup that exposes only an `access_denied` result.
3. Malformed tool-call arguments that escalate without another model call.
4. A two-turn conversation that passes the saved response ID into the follow-up request.
5. A missing order ID that receives text only and does not call a tool.
6. A refund request that does not promise a refund and directs the case to human review.
7. A delivered-but-missing package that uses verified `delivered` evidence and escalates.

The full project suite now has **20 passing tests**:

- 8 deterministic-agent tests
- 5 backend-tool tests
- 7 LLM integration tests using a fake client

Run the suite:

```bash
cd /Users/hanwang/Learn/agent-learning-notes/order-agent
PYTHONPATH="$(pwd)/src" python3 -m unittest discover -s tests -v
```

## Takeaways

1. Conversation memory improves usability, but backend authorization must remain independent of it.
2. Model output is variable, so tests should check observable outcomes: tool calls, safe evidence flow, escalation, and forbidden claims.
3. Fake model clients are a practical way to test agent orchestration without API cost or network dependence.
4. The agent now supports a realistic support conversation while retaining a narrow, read-only tool boundary.

## Next topic

Design a small evaluation dataset and rubric that can assess multiple customer phrasings, rather than only one hand-written test per policy case.
