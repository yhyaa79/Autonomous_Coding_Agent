from pathlib import Path

from .ignore import should_skip_dir, should_skip_file
from .scope import path_in_scope
from .workspace import resolve_in_workspace


def build_tree_node(
    workspace_root: Path,
    path: str = ".",
    depth: int = 2,
    scope_paths: list[str] | None = None,
) -> dict:
    root = workspace_root.resolve()
    target = resolve_in_workspace(root, path)
    scopes = scope_paths or []

    def node_at(p: Path, level: int) -> dict:
        rel = p.relative_to(root).as_posix() if p != root else ""
        name = p.name if p != root else root.name
        entry: dict = {
            "name": name,
            "path": rel or ".",
            "type": "dir" if p.is_dir() else "file",
            "in_scope": path_in_scope(rel or ".", scopes) if scopes else True,
        }
        if p.is_dir() and level < depth:
            children = []
            try:
                items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except OSError:
                items = []
            for child in items[:200]:
                if child.is_dir() and should_skip_dir(child.name):
                    continue
                if child.is_file() and should_skip_file(child):
                    continue
                child_rel = child.relative_to(root).as_posix()
                if scopes and not path_in_scope(child_rel, scopes):
                    entry_scope_child = False
                else:
                    entry_scope_child = True
                ch = node_at(child, level + 1)
                ch["in_scope"] = entry_scope_child
                children.append(ch)
            entry["children"] = children
        return entry

    if target.is_file():
        rel = target.relative_to(root).as_posix()
        return {
            "name": target.name,
            "path": rel,
            "type": "file",
            "in_scope": path_in_scope(rel, scopes) if scopes else True,
        }
    return node_at(target, 0)
