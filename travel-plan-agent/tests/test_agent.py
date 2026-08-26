from agent import load_system_prompt


def test_system_prompt_contains_safety_rules() -> None:
    prompt = load_system_prompt()
    assert "Do not make bookings" in prompt
    assert "assumptions" in prompt.lower()
