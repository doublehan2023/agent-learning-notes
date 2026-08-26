"""Command-line interface for TravelPlanAgent."""

from agent import TravelPlanAgent


def main() -> None:
    agent = TravelPlanAgent()
    print("TravelPlanAgent — describe the trip you want to plan. Type 'quit' to exit.")

    while True:
        user_message = input("\nYou: ").strip()
        if user_message.lower() in {"quit", "exit"}:
            break
        if not user_message:
            continue
        print(f"\nTravelPlanAgent: {agent.respond(user_message)}")


if __name__ == "__main__":
    main()
