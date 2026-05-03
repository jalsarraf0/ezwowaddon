"""Package entry point. Routes to CLI or GUI based on argv."""

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


if __name__ == "__main__":
    raise SystemExit(main())
