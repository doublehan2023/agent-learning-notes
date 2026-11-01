# Shared Evals and Live Smoke Tests

**Date:** 2026-11-01  
**Focus:** Turn the order-agent eval dataset into a shared contract for deterministic and LLM agent implementations.

## What I built

The order agent now uses one dataset of **18 cases** for both implementations:

```text
cases.json
   ├─ deterministic agent runner
   └─ mocked LLM agent runner
```

Each case defines the customer message, authenticated customer, expected tool call,
required outcomes, and forbidden outcomes. The same grader checks whether the agent
used the correct tool, sent the correct order ID, followed escalation rules, and
avoided unsafe claims.

## Decision rules made explicit

The order-status policy now has a clear precedence order:

1. A refund request escalates immediately without a lookup.
2. Multiple **distinct** order IDs require clarification without a lookup.
3. No order ID requires asking the customer for one.
4. Exactly one order ID permits one status lookup.

Repeated mentions of the same ID count as one order. The agent also recognizes an
ID written as `order 123`, not only `#123`.

## Evals added

Five useful input and policy cases were added:

- An order ID without `#`.
- The same order ID repeated in a message.
- Two different order IDs across separate sentences.
- A customer saying a delivered order “never arrived.”
- A delayed order combined with a refund request, confirming that refund escalation
  takes priority over lookup.

The suite now has **25 passing unit tests** and **18/18 passing deterministic evals**.

## Mocked LLM evaluation

The runner supports a mocked LLM mode:

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py --agent llm-mocked
```

This mode does not call a model or spend API credits. It supplies controlled model
responses and verifies the LLM agent loop: function-call parsing, authorization,
tool arguments, safe tool-result handling, and final-response grading.

It is valuable because it is fast and repeatable, but it does **not** prove a real
model will select the intended tool or policy response. Both deterministic and
mocked LLM runs pass **18/18** cases.

## Live smoke-test mode

I added a limited live mode that is intentionally restricted to five high-value
cases: normal lookup, unauthorized lookup, refund request, multiple IDs, and
delivered-but-missing.

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py --agent llm-live
```

It prints the model's actual tool calls, arguments, escalation state, and final
response. This is the proper next check because models are variable and real API
behavior can differ from a fixture.

The OpenAI Python SDK is installed, but I did not make a live request today: the
environment does not have `OPENAI_API_KEY`. Set the key in the terminal before
running this mode. Never commit an API key to the repository.

## Gemini API key decision

A Gemini key cannot authenticate directly to the current OpenAI Responses API
client. Gemini provides an OpenAI-compatible endpoint, but it uses a different
base URL and model configuration. If I use Gemini later, I should add it as a
separate provider option rather than mixing credentials into the OpenAI path.

## Key takeaways

1. The eval dataset is a behavioral contract, not merely a collection of tests.
2. Mocked evaluations test orchestration deterministically; live evaluations test
   a model's real decisions and should start with a small, high-value suite.
3. Tool correctness includes both selecting the tool and supplying safe, accurate
   arguments.
4. Explicit precedence rules prevent ambiguous behavior when several policy
   conditions appear in one message.

The focus on tool selection, tool arguments, and edge cases follows [OpenAI
evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Next topic

Run the five-case live smoke suite after setting an API key. Review any failure by
separating it into one of four causes: unclear instructions, incorrect tool call,
missing guardrail, or unclear evaluator.
