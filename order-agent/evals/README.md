# Order-agent evals

Run the local deterministic evaluation suite with:

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py
```

Run the same dataset through the LLM agent's mocked Responses API loop with:

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py --agent llm-mocked
```

`llm-mocked` never calls the OpenAI API. Each case includes fixture model
responses so this mode verifies tool calls, tool arguments, tool-result handling,
and final policy behavior deterministically. A future live smoke suite can reuse
the same cases with a real model.

## Live smoke suite

After setting `OPENAI_API_KEY`, run five selected high-value cases against the
real model:

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py --agent llm-live
```

This mode makes paid API requests and is intentionally restricted to the five
smoke cases: a normal lookup, unauthorized lookup, refund request, multiple IDs,
and delivered-but-missing report. To run one of them while debugging:

```bash
PYTHONPATH="$(pwd)/src" python3 evals/run_evals.py --agent llm-live \
  --case multiple-order-ids-01
```

The runner prints each live tool call, its arguments, escalation state, and final
response. It will not run arbitrary cases in live mode.

## Decision precedence

1. Refund request: escalate immediately; do not call the order-status tool.
2. Multiple distinct order IDs: ask which order to check; do not call the tool.
3. No order ID: ask for an ID; do not call the tool.
4. Exactly one order ID: call `get_order_status` once.

Repeated mentions of the same order ID count as one ID. The runner prints the
customer message, expected and actual tool behavior, response, and escalation
reason whenever a case fails.
