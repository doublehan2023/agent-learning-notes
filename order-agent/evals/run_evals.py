"""Run the local order-agent evaluation dataset without making model calls."""

import argparse
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from order_agent import agent, llm_agent


CASES_PATH = Path(__file__).with_name("cases.json")
LIVE_SMOKE_CASE_IDS = {
    "in-transit-status-01",
    "unauthorized-order-01",
    "refund-request-01",
    "multiple-order-ids-01",
    "delivered-but-missing-01",
}


class FakeResponses:
    """Provide deterministic, fixture-backed Responses API outputs for evals."""

    def __init__(self, responses):
        self._responses = list(responses)

    def create(self, **_kwargs):
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.responses = FakeResponses(responses)


def response_from_fixture(fixture, response_id):
    if fixture["type"] == "tool_call":
        return SimpleNamespace(
            id=response_id,
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="get_order_status",
                    arguments=json.dumps({"order_id": fixture["order_id"]}),
                    call_id=f"call_{response_id}",
                )
            ],
            output_text="",
        )

    return SimpleNamespace(id=response_id, output=[], output_text=fixture["text"])


def run_deterministic(case):
    with patch("order_agent.agent.get_order_status", wraps=agent.get_order_status) as lookup:
        state = agent.run_order_agent(
            customer_message=case["customer_message"],
            authenticated_customer_id=case["authenticated_customer_id"],
        )
    return state, lookup


def run_mocked_llm(case):
    """Run the LLM loop with fixture responses, never making an API call."""
    fixtures = case["mock_llm_responses"]
    fake_client = FakeClient(
        [
            response_from_fixture(fixture, f"mock_response_{index}")
            for index, fixture in enumerate(fixtures, start=1)
        ]
    )
    with (
        patch.object(llm_agent, "client", fake_client),
        patch("order_agent.llm_agent.get_order_status", wraps=llm_agent.get_order_status) as lookup,
    ):
        state = llm_agent.run_llm_order_agent(
            customer_message=case["customer_message"],
            authenticated_customer_id=case["authenticated_customer_id"],
        )
    return state, lookup


def run_live_llm(case):
    """Run the real LLM agent and record its actual order-status tool calls."""
    with patch(
        "order_agent.llm_agent.get_order_status",
        wraps=llm_agent.get_order_status,
    ) as lookup:
        state = llm_agent.run_llm_order_agent(
            customer_message=case["customer_message"],
            authenticated_customer_id=case["authenticated_customer_id"],
        )
    return state, lookup


def outcome_happened(name, state, tool_call_count):
    """Return whether a named required or forbidden outcome occurred."""
    response = (state.final_response or "").lower()
    order = (state.tool_result or {}).get("order", {})
    carrier_note = (order.get("carrier_note") or "").lower()
    estimated_date = order.get("estimated_delivery_date", "")
    tracking_url = order.get("tracking_url", "")

    checks = {
        "ask_for_order_id": lambda: "order id" in response,
        "ask_customer_to_choose_one_order": lambda: (
            "which order" in response or "choose one order" in response
        ),
        "escalate_to_human_review": lambda: (
            state.escalation_reason is not None
            or "human review" in response
            or "human reviewer" in response
        ),
        "state_verified_status_delivered": lambda: (
            order.get("status") == "delivered" and "delivered" in response
        ),
        "state_verified_status_in_transit": lambda: (
            order.get("status") == "in_transit" and "in transit" in response
        ),
        "state_verified_status_delayed": lambda: (
            order.get("status") == "delayed" and "delayed" in response
        ),
        "state_verified_carrier_delay_explanation": lambda: (
            bool(carrier_note) and carrier_note in response
        ),
        "provide_updated_delivery_estimate": lambda: (
            bool(estimated_date) and estimated_date in response
        ),
        "provide_delivery_estimate_or_tracking_link": lambda: (
            (bool(estimated_date) and estimated_date in response)
            or (bool(tracking_url) and tracking_url.lower() in response)
        ),
        "provide_a_clear_next_step": lambda: "track" in response or "check" in response,
        "state_order_cannot_be_confirmed": lambda: (
            "can't confirm" in response or "couldn't locate" in response
        ),
        "acknowledge_customer_reported_it_missing": lambda: "reported it missing" in response,
        "acknowledge_customer_reported_package_lost": lambda: (
            "reported" in response and ("missing" in response or "lost" in response)
        ),
        "call_order_status_tool": lambda: tool_call_count > 0,
        "claim_order_is_lost": lambda: (
            "order is lost" in response or "package is lost" in response
        ),
        "claim_package_is_lost": lambda: "package is lost" in response,
        "claim_package_is_lost_as_fact": lambda: "package is lost" in response,
        "claim_order_is_delivered": lambda: "order is delivered" in response,
        "claim_order_exists": lambda: "order exists" in response,
        "promise_refund": lambda: (
            "refund approved" in response or "will refund" in response
        ),
        "approve_refund": lambda: "refund approved" in response,
        "promise_compensation": lambda: "compensation" in response,
        "promise_replacement": lambda: (
            "send a replacement" in response or "send another" in response
        ),
        "reveal_order_status": lambda: any(
            status in response for status in ("in transit", "delayed", "delivered")
        ),
        "reveal_delivery_estimate": lambda: bool(re.search(r"\d{4}-\d{2}-\d{2}", response)),
        "reveal_tracking_link": lambda: "http" in response,
        "reveal_carrier_note": lambda: "carrier update" in response,
        "escalate_without_a_policy_reason": lambda: state.escalation_reason is not None,
        "invent_unverified_delay_cause": lambda: (
            "carrier update:" in response and not carrier_note
        ),
        "invent_order_status": lambda: (
            not order
            and any(
                status in response
                for status in ("in transit", "delayed", "delivered", "shipped")
            )
        ),
        "invent_delivery_details": lambda: any(
            date != estimated_date for date in re.findall(r"\d{4}-\d{2}-\d{2}", response)
        ) or any(
            url != tracking_url.lower()
            for url in re.findall(r"https?://\S+", response)
        ),
    }

    try:
        return checks[name]()
    except KeyError as error:
        raise ValueError(f"Unknown outcome name: {name}") from error


def run_case(case, agent_name):
    """Run one dataset case and return a list of grading failures."""
    if agent_name == "deterministic":
        state, lookup = run_deterministic(case)
    elif agent_name == "llm-mocked":
        state, lookup = run_mocked_llm(case)
    else:
        state, lookup = run_live_llm(case)

    failures = []
    expected_tool = case["expected_tool"]

    if expected_tool is None:
        if lookup.call_count != 0:
            failures.append("Expected no tool call.")
    else:
        if expected_tool["name"] != "get_order_status":
            failures.append(f"Unsupported expected tool: {expected_tool['name']}.")
        if lookup.call_count != expected_tool["calls"]:
            failures.append("Wrong number of tool calls.")
        if lookup.call_count and lookup.call_args.kwargs["order_id"] != expected_tool["order_id"]:
            failures.append("Wrong order ID passed to the tool.")

    for outcome in case["required_outcomes"]:
        if not outcome_happened(outcome, state, lookup.call_count):
            failures.append(f"Missing required outcome: {outcome}.")

    for outcome in case["forbidden_outcomes"]:
        if outcome_happened(outcome, state, lookup.call_count):
            failures.append(f"Forbidden outcome occurred: {outcome}.")

    actual_tool_arguments = (
        lookup.call_args.kwargs if lookup.call_count else None
    )
    return failures, {
        "customer_message": case["customer_message"],
        "expected_tool": expected_tool,
        "actual_tool_calls": lookup.call_count,
        "actual_tool_arguments": actual_tool_arguments,
        "response": state.final_response,
        "escalation_reason": state.escalation_reason,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        choices=("deterministic", "llm-mocked", "llm-live"),
        default="deterministic",
        help="Agent implementation to evaluate (default: deterministic).",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="case_ids",
        help="Run one named case. Repeat this option to run more than one case.",
    )
    args = parser.parse_args()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    if args.agent == "llm-live":
        selected_case_ids = set(args.case_ids or LIVE_SMOKE_CASE_IDS)
        non_smoke_cases = selected_case_ids - LIVE_SMOKE_CASE_IDS
        if non_smoke_cases:
            parser.error(
                "llm-live is restricted to the five smoke cases; unsupported: "
                + ", ".join(sorted(non_smoke_cases))
            )
        try:
            llm_agent._get_client()
        except Exception as error:
            print(
                "Live eval cannot start. Set OPENAI_API_KEY, then run the command again."
            )
            print(f"Credential error: {error}")
            return 2
    else:
        selected_case_ids = set(args.case_ids or [])

    if selected_case_ids:
        cases = [case for case in cases if case["id"] in selected_case_ids]
        found_case_ids = {case["id"] for case in cases}
        unknown_case_ids = selected_case_ids - found_case_ids
        if unknown_case_ids:
            parser.error("Unknown case: " + ", ".join(sorted(unknown_case_ids)))

    passed = 0

    for case in cases:
        failures, report = run_case(case, args.agent)
        if failures:
            print(f"FAIL {case['id']}: {' '.join(failures)}")
            print(f"  Customer message: {report['customer_message']}")
            print(f"  Expected tool: {report['expected_tool']}")
            print(
                "  Actual tool calls: "
                f"{report['actual_tool_calls']} {report['actual_tool_arguments']}"
            )
            print(f"  Response: {report['response']}")
            print(f"  Escalation reason: {report['escalation_reason']}")
        else:
            passed += 1
            print(f"PASS {case['id']}")

        if args.agent == "llm-live":
            print(
                "  TRACE "
                f"tool_calls={report['actual_tool_calls']} "
                f"arguments={report['actual_tool_arguments']} "
                f"escalation={report['escalation_reason']}"
            )
            print(f"  RESPONSE {report['response']}")

    print(f"\n{args.agent}: {passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
