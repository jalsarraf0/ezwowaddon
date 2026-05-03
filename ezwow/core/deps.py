"""Topologically resolve addon dependencies."""

from __future__ import annotations

from ezwow.catalog.schema import Catalog


class CycleError(RuntimeError):
    """Raised when the dependency graph contains a cycle."""


def resolve(addon_ids: list[str], catalog: Catalog) -> list[str]:
    """Return addon_ids in dependency-first install order. Pulls transitive deps."""
    by_id = {a.id: a for a in catalog.addons}
    for aid in addon_ids:
        if aid not in by_id:
            raise KeyError(f"unknown addon id {aid!r}")

    ordered: list[str] = []
    visited: set[str] = set()
    on_stack: set[str] = set()

    def visit(aid: str, stack: tuple[str, ...]) -> None:
        if aid in visited:
            return
        if aid in on_stack:
            cycle = " -> ".join((*stack, aid))
            raise CycleError(f"dependency cycle: {cycle}")
        if aid not in by_id:
            raise KeyError(f"unknown addon id {aid!r}")
        on_stack.add(aid)
        for dep in by_id[aid].depends:
            visit(dep, (*stack, aid))
        on_stack.discard(aid)
        visited.add(aid)
        ordered.append(aid)

    for aid in addon_ids:
        visit(aid, ())
    return ordered
