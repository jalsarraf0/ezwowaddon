"""Enables `python -m ezwow`. Delegates to ezwow._entry.main."""

from __future__ import annotations

from ezwow._entry import main

if __name__ == "__main__":
    raise SystemExit(main())
