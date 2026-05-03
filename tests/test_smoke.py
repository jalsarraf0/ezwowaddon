import importlib

import ezwow


def test_version_string_present():
    assert isinstance(ezwow.__version__, str)
    assert ezwow.__version__.count(".") == 2


def test_subpackages_importable():
    for mod in (
        "ezwow",
        "ezwow.catalog",
        "ezwow.core",
        "ezwow.ui",
        "ezwow.cli",
    ):
        importlib.import_module(mod)
