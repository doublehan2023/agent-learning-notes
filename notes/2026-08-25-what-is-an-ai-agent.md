# What Is an AI Agent?

**Date:** 2026-08-25  
**Focus:** What AI agents are and the main ways to classify them.

## Core definition

An AI agent is a system that works toward a goal on a user's behalf with some independence. It can decide what to do next, use tools to gather information or take actions, and continue through a workflow until it reaches a result or needs to hand control back to the user.

```text
Goal → decide → use tools / take action → inspect result → repeat or finish
```

The three core building blocks are:

- **Model:** the LLM that reasons and makes decisions.
- **Tools:** functions or external systems used to retrieve information or take action.
- **Instructions and guardrails:** rules that define acceptable behavior and limits.

Source: [OpenAI, *A practical guide to building agents*](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/).

## Agent vs. chatbot

A regular chatbot can answer a question. An agent can manage a workflow.

| System | Agent? | Reason |
| --- | --- | --- |
| FAQ chatbot | Usually no | It responds, but does not control a workflow. |
| One-shot text summarizer | No | It performs one fixed task. |
| Weather chatbot that only displays a forecast | No | It gives a fixed response to a request. |
| Weather assistant that plans a commute | Yes | It can check weather, calendar, location, and routes to recommend what to bring or when to leave. |

**Important:** Access to tools alone does not make a system an agent. The system must use judgment to choose actions toward a goal.

## Main types of agents

### 1. Reactive agents

Reactive agents respond to the current input with a direct rule or narrow decision.

```text
Input → rule / decision → response or action
```

Example: If the temperature is below 5°C, recommend wearing a coat.

They are usually fast and predictable, but do not create an extended plan.

### 2. Goal-based agents

Goal-based agents choose actions based on the outcome they need to reach.

Example: Find a flight that meets a user's dates, budget, and preferences.

### 3. Planning agents

Planning agents break a larger goal into steps, perform those steps, check results, and adapt when needed.

```text
Goal → plan → act → inspect → adjust → finish
```

Example goal: “Help me get to work on time tomorrow.”

Possible workflow:

1. Check the calendar for the start time.
2. Check weather for the departure window.
3. Check traffic or transit conditions.
4. Recommend a departure time and what to bring.

### 4. Tool-using agents

Tool-using agents retrieve information or take action through external tools, such as web search, files, databases, email, calendars, or APIs. This is commonly a capability of goal-based and planning agents rather than a completely separate category.

### 5. Single-agent systems

One agent owns the workflow and uses its tools to complete the task.

```text
User → one agent → tools → result
```

Start here whenever possible. A single agent is easier to build, test, and maintain.

### 6. Multi-agent systems

Multiple specialized agents coordinate on one workflow.

```text
User → coordinator → research agent
                  → booking agent
                  → writing agent
                  → combined result
```

Common patterns:

- **Manager pattern:** a central agent delegates to specialist agents and combines the results.
- **Handoff pattern:** agents pass execution to another agent when another specialty is needed.

Use multi-agent systems only when one agent becomes too complicated, struggles with many overlapping tools, or needs clearly separate areas of expertise.

### 7. Human-in-the-loop agents

A person reviews or approves important actions before the agent performs them. This is useful for sensitive, costly, or irreversible actions.

Example: An email agent reads unread messages, identifies urgent ones, drafts replies, then asks the user to approve each message before sending.

## Key comparisons

| | Reactive agent | Planning agent |
| --- | --- | --- |
| Focus | Immediate input | End goal |
| Steps | Usually one | Often many |
| Adjusts after results | Limited | Yes |
| Example | “Is it raining?” | “Plan my commute.” |

## Takeaways

1. An agent does more than generate text: it manages a workflow toward a goal.
2. It uses a model, tools, and instructions/guardrails.
3. A chatbot becomes agent-like when it can select and perform actions based on context and goals.
4. Planning agents handle multi-step work and adapt based on results.
5. Start with a single agent; use multiple agents only when the complexity genuinely requires it.
6. Human approval is an important safety mechanism for consequential actions.

## Examples discussed today

- A forecast-only weather chatbot is not an agent.
- A weather assistant that checks weather, calendar, and route conditions to help with a commute is an agent.
- An assistant that reads email, identifies urgency, drafts replies, and asks for approval is a planning, single-agent, human-in-the-loop system.

## Next topics

- When an agent is better than a deterministic workflow
- Tools, instructions, and guardrails in more depth
- A small first agent project
