from pathlib import Path

from agent.store import AGENT_STORE_DIR

CUSTOM_ROOT = f"{AGENT_STORE_DIR}/runtime/custom_tools"
MANIFEST = f"{CUSTOM_ROOT}/manifest.json"
TOOLS_DIR = f"{CUSTOM_ROOT}/tools"


def custom_tools_dir(workspace: Path) -> Path:
    return workspace / CUSTOM_ROOT


def manifest_path(workspace: Path) -> Path:
    return workspace / MANIFEST


def tool_module_path(workspace: Path, tool_id: str) -> Path:
    return workspace / TOOLS_DIR / f"{tool_id}.py"
