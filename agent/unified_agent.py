"""سازگاری با importهای قدیمی — agentها در agent/agents/ ثبت می‌شوند."""

from agent import agents as _agents  # noqa: F401

__all__ = ["_agents"]
