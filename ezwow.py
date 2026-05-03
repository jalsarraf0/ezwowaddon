"""Legacy entry point for backwards compatibility.

The real package lives in `ezwow/`. PyInstaller and direct
`python ezwow.py` invocations route through here.
"""

from __future__ import annotations

import sys

from ezwow.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
