"""Headless command-line interface for ezwowaddon."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import pathlib
import shutil
import sys
from collections.abc import Sequence

from ezwow import __version__, config
from ezwow.catalog import loader as catalog_loader
from ezwow.core import (
    backup,
    deps,
    detector,
    github,
    installer,
    manifest,
    profile,
    updater,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ezwow",
        description=f"EZWowAddon {__version__} — Turtle WoW addon manager",
    )
    p.add_argument("--gui", "-g", action="store_true", help="launch the graphical UI")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("list", help="list addons")
    sp.add_argument("--installed", action="store_true")
    sp.add_argument("--updates", action="store_true")

    sp = sub.add_parser("install", help="install one or more addons by id")
    sp.add_argument("ids", nargs="*")
    sp.add_argument("--preset", help="apply a preset by id")

    sp = sub.add_parser("update", help="update addons")
    sp.add_argument("ids", nargs="*")
    sp.add_argument("--all", action="store_true")

    sp = sub.add_parser("remove", help="uninstall an addon")
    sp.add_argument("id")

    sp = sub.add_parser("backup", help="snapshot AddOns + SavedVariables")
    sp.add_argument("--out", default=None)

    sp = sub.add_parser("restore", help="restore from a backup")
    sp.add_argument("path")

    sp = sub.add_parser("profile", help="export/import profiles")
    sp.add_argument("action", choices=("export", "import"))
    sp.add_argument("path")

    sub.add_parser("doctor", help="diagnostic info")

    return p


def run(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = _build_parser()
    args = parser.parse_args(list(argv))

    if args.cmd is None:
        parser.print_help()
        return 1

    if args.cmd == "list":
        return _cmd_list(args)
    if args.cmd == "install":
        return _cmd_install(args)
    if args.cmd == "update":
        return _cmd_update(args)
    if args.cmd == "remove":
        return _cmd_remove(args)
    if args.cmd == "backup":
        return _cmd_backup(args)
    if args.cmd == "restore":
        return _cmd_restore(args)
    if args.cmd == "profile":
        return _cmd_profile(args)
    if args.cmd == "doctor":
        return _cmd_doctor()
    return 1


def _addons_folder(cfg: config.UserConfig) -> pathlib.Path | None:
    return detector.find_addons_folder(saved=cfg.addons_folder)


def _cmd_list(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)

    if args.installed:
        if not folder:
            print("AddOns folder not configured", file=sys.stderr)
            return 3
        m = manifest.load(folder)
        for inst in sorted(m.installs.values(), key=lambda i: i.addon_id):
            sha_display = (inst.sha or "unknown")[:7]
            print(f"{inst.addon_id:30s}  ref={inst.ref}  sha={sha_display}")
        return 0

    if args.updates:
        if not folder:
            print("AddOns folder not configured", file=sys.stderr)
            return 3
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(addons_folder=folder, catalog=cat, gh_client=gh)
        for u in plan.updates:
            cur = (u.current or "?")[:7]
            lat = (u.latest or "?")[:7]
            print(f"{u.addon_id:30s}  {cur} -> {lat}")
        return 0

    by_cat: dict[str, list[str]] = {}
    for a in cat.addons:
        by_cat.setdefault(a.category, []).append(a.id)
    for cat_id in sorted(by_cat):
        print(f"\n[{cat_id}]")
        for aid in sorted(by_cat[cat_id]):
            print(f"  {aid}")
    return 0


def _do_install_ids(addon_ids: list[str]) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        print("AddOns folder not configured", file=sys.stderr)
        return 3

    try:
        ordered = deps.resolve(addon_ids, cat)
    except (deps.CycleError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
    for aid in ordered:
        addon = cat.addon_by_id(aid)
        if addon is None:
            continue
        url = addon.branch_zip_url()
        print(f"installing {aid} from {url}")
        try:
            result = installer.install_from_url(
                url=url, addons_folder=folder, target_folder_name=addon.folder
            )
        except installer.InstallError as exc:
            print(f"error installing {aid}: {exc}", file=sys.stderr)
            return 2
        sha = gh.branch_head_sha(addon.github, addon.branch)
        manifest.record(
            folder,
            manifest.InstallEntry(
                addon_id=aid,
                folder=addon.folder,
                source=f"github:{addon.github}",
                ref=addon.branch,
                sha=sha,
                installed_at=dt.datetime.now(dt.UTC),
                files=result.files,
                size_bytes=result.size_bytes,
            ),
        )
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    requested: list[str] = list(args.ids)
    if args.preset:
        try:
            resolved = profile.resolve_preset(args.preset, cat)
        except KeyError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 4
        requested.extend(resolved.addon_ids)

    if not requested:
        print("nothing to install (provide ids or --preset)", file=sys.stderr)
        return 1

    return _do_install_ids(requested)


def _cmd_update(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
    plan = updater.plan(addons_folder=folder, catalog=cat, gh_client=gh)
    targets: list[str]
    if args.all:
        targets = [u.addon_id for u in plan.updates]
    else:
        wanted = set(args.ids)
        targets = [u.addon_id for u in plan.updates if u.addon_id in wanted]
    if not targets:
        print("nothing to update")
        return 0
    return _do_install_ids(targets)


def _cmd_remove(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    m = manifest.load(folder)
    entry = m.installs.get(args.id)
    if entry is None:
        print(f"{args.id} not installed", file=sys.stderr)
        return 1
    target = folder / entry.folder
    if target.is_dir():
        shutil.rmtree(target)
    manifest.remove(folder, args.id)
    print(f"removed {args.id}")
    return 0


def _cmd_backup(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    wow_root = folder.parent.parent
    out_dir = pathlib.Path(args.out) if args.out else config.data_dir() / "backups"
    archive = backup.create_backup(wow_root=wow_root, out_dir=out_dir)
    print(archive)
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    backup.restore_backup(archive=pathlib.Path(args.path), wow_root=folder.parent.parent)
    return 0


def _cmd_profile(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    if args.action == "export":
        m = manifest.load(folder)
        ids = sorted(m.installs.keys())
        profile.export_profile(
            out_path=pathlib.Path(args.path),
            addon_ids=ids,
            client_mod_ids=[],
            label="user-export",
        )
        return 0
    p = profile.import_profile(pathlib.Path(args.path))
    return _do_install_ids(p.addons)


def _cmd_doctor() -> int:
    cfg = config.load()
    folder = detector.find_addons_folder(saved=cfg.addons_folder)
    print(f"version       {__version__}")
    print(f"config        {config.config_path()}")
    print(f"cache         {config.cache_dir()}")
    print(f"data          {config.data_dir()}")
    print(f"addons folder {folder or '(not found)'}")
    if folder:
        m = manifest.load(folder)
        print(f"installs      {len(m.installs)}")
    return 0
