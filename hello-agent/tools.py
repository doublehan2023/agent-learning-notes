"""Local tool registration and lookup, independent of LLM providers."""

from collections.abc import Callable
from typing import Any


class ToolExecutor:
    """Register application tools and retrieve them by name."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def registerTool(self, name: str, desc: str, func: Callable[..., Any]) -> None:
        """Register a tool, replacing a previous tool with the same name."""
        if name in self.tools:
            print(f"Warning: Tool '{name}' already exists and will be overwritten.")
        self.tools[name] = {"description": desc, "func": func}
        print(f"Tool '{name}' registered.")

    def getTool(self, name: str) -> Callable[..., Any] | None:
        """Return a tool's function, or ``None`` when it is not registered."""
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """Return a formatted description of all registered tools."""
        return "\n".join(
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        )
