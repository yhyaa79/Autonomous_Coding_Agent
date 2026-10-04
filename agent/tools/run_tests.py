from agent.extra_impl import run_tests
from agent.tools.base import define_tool

define_tool(
    "run_tests",
    "Run tests (auto-detect pytest/Django/npm if command omitted).",
    {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Optional full test command"},
            "cwd": {"type": "string", "default": "."},
        },
        "required": [],
    },
    lambda a, o: run_tests(a.get("command"), o, a.get("cwd", ".")),
)
