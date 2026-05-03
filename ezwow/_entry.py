"""Package entry point function. Imported by both `ezwow.__main__` (for `python -m ezwow`) and `ezwow` (top-level re-export). Lives in its own module so static analyzers can resolve `from ezwow import main` cleanly."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"--gui", "-g"}:
        from ezwow.cli import run

        return run(args)
    from ezwow.ui.app import launch

    launch()
    return 0
