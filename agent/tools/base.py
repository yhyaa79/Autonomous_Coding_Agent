"""پایهٔ مشترک ابزارها — هر ابزار در فایل جدا با define_tool یا BaseTool ثبت می‌شود."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from agent.options import AgentOptions
from agent.tool_registry import register_tool

ToolRunner = Callable[[dict[str, Any], AgentOptions], str]


class BaseTool(ABC):
    """کلاس پایه: subclass کنید و name، description، parameters و run را پیاده کنید."""

    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    def run(self, arguments: dict[str, Any], options: AgentOptions) -> str:
        raise NotImplementedError

    def openai_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def register(self) -> None:
        register_tool(
            self.name,
            self.openai_definition(),
            lambda _n, args, opts: self.run(args, opts),
        )


def define_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    handler: ToolRunner,
) -> None:
    """ثبت سریع یک ابزار تابعی — برای فایل‌های تک‌ابزار."""
    register_tool(
        name,
        {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        },
        lambda _n, args, opts: handler(args, opts),
    )
