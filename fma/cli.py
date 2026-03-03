from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import FMAConfig, DEFAULT_RULES, load_config, write_example_config
from .organizer import apply_moves, plan_moves, rollback_from_undo, scan_directory

DEFAULT_PROJECT_INCLUDES = ["*.py", "*.js", "*.ts", "*.tsx", "*.jsx"]
DEFAULT_PROJECT_EXCLUDES = [
    "*/.git/*",
    "*/node_modules/*",
    "*/.next/*",
    "*/dist/*",
    "*/build/*",
    "*/coverage/*",
    "*/venv/*",
    "*/.venv/*",
]


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-config":
        config_path = Path(args.path)
        if config_path.exists() and not args.force:
            print(f"Config already exists: {config_path}. Use --force to overwrite.")
            return 1
        write_example_config(config_path)
        print(f"Wrote example config to {config_path}")
        return 0

    if args.command == "rollback":
        restored = rollback_from_undo(Path(args.undo_file).expanduser().resolve(), dry_run=args.dry_run)
        mode = "Dry-run rollback" if args.dry_run else "Rollback"
        print(f"{mode} complete: {restored} files affected.")
        _log(args.log_file, f"{mode}: {restored} files from {args.undo_file}")
        return 0

    if args.command == "quick-project":
        return _run_quick_project(args)

    config = _resolve_config(args)

    if args.command == "scan":
        results = scan_directory(config.source_dir, recursive=args.recursive)
        print(json.dumps([asdict(x) for x in results], indent=2))
        _log(args.log_file, f"Scan complete: {len(results)} files from {config.source_dir}")
        return 0

    if args.command == "organize":
        planned = plan_moves(
            config.source_dir,
            config.destination_dir,
            config.rules,
            recursive=args.recursive,
            mode=args.mode,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            max_files=args.max_files,
        )

        if args.dry_run:
            print(json.dumps([asdict(x) for x in planned], indent=2))
            action_word = "copied" if args.operation == "copy" else "moved"
            print(f"\nDry run complete: {len(planned)} files would be {action_word}.")
            _log(args.log_file, f"Dry-run organize ({args.operation}): {len(planned)} planned")
            return 0

        if args.max_files is None and len(planned) > 1000:
            print(
                "Safety stop: planned moves exceed 1000 files. "
                "Use --max-files to set a cap, or review with --dry-run first."
            )
            _log(args.log_file, "Safety stop triggered: >1000 planned without --max-files")
            return 1

        undo_path = Path(args.undo_file).expanduser().resolve()
        moved = apply_moves(planned, undo_file=undo_path, operation=args.operation)
        print(f"Applied {moved} {args.operation}(s).")
        print(f"Undo map written to: {undo_path}")
        _log(args.log_file, f"Apply organize ({args.operation}): {moved} files, undo={undo_path}")
        return 0

    parser.print_help()
    return 1


def _run_quick_project(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve() if args.destination else source / "sorted-preview"

    planned = plan_moves(
        source,
        destination,
        DEFAULT_RULES,
        recursive=True,
        mode="extension",
        include_patterns=DEFAULT_PROJECT_INCLUDES,
        exclude_patterns=DEFAULT_PROJECT_EXCLUDES,
        max_files=args.max_files,
    )

    if not args.apply:
        print(json.dumps([asdict(x) for x in planned], indent=2))
        print(f"\nQuick project dry run: {len(planned)} files would be copied.")
        print("Use --apply to execute.")
        _log(args.log_file, f"Quick project dry-run: {len(planned)} planned from {source}")
        return 0

    undo_path = Path(args.undo_file).expanduser().resolve()
    copied = apply_moves(planned, undo_file=undo_path, operation="copy")
    print(f"Quick project apply complete: copied {copied} files.")
    print(f"Destination: {destination}")
    print(f"Undo map: {undo_path}")
    _log(args.log_file, f"Quick project apply: {copied} copied from {source} to {destination}")
    return 0


def _resolve_config(args: argparse.Namespace) -> FMAConfig:
    if args.config:
        return load_config(Path(args.config).expanduser().resolve())

    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve() if args.destination else source
    return FMAConfig(source_dir=source, destination_dir=destination, rules=DEFAULT_RULES)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fma", description="File Management Automation MVP")
    sub = parser.add_subparsers(dest="command")

    init_cmd = sub.add_parser("init-config", help="Write an example JSON config")
    init_cmd.add_argument("--path", default="fma-config.json", help="Where to write the config")
    init_cmd.add_argument("--force", action="store_true", help="Overwrite if config already exists")

    scan_cmd = sub.add_parser("scan", help="Scan and print file metadata as JSON")
    _add_common_flags(scan_cmd)
    scan_cmd.add_argument("--recursive", action="store_true", help="Scan directories recursively")

    org_cmd = sub.add_parser("organize", help="Organize files")
    _add_common_flags(org_cmd)
    org_cmd.add_argument("--dry-run", action="store_true", help="Preview changes without moving/copying files")
    org_cmd.add_argument("--undo-file", default="./fma-undo.json", help="Where to save move manifest")
    org_cmd.add_argument("--recursive", action="store_true", help="Organize files recursively")
    org_cmd.add_argument("--mode", choices=["extension", "date"], default="extension", help="Organization mode")
    org_cmd.add_argument("--include", action="append", default=[], help="Glob include filter (repeatable)")
    org_cmd.add_argument("--exclude", action="append", default=[], help="Glob exclude filter (repeatable)")
    org_cmd.add_argument("--max-files", type=int, help="Maximum files to process in this run")
    org_cmd.add_argument("--operation", choices=["move", "copy"], default="move", help="Whether to move or copy files")

    quick_cmd = sub.add_parser("quick-project", help="One-command preset for coding project folders")
    quick_cmd.add_argument("--source", required=True, help="Project folder root")
    quick_cmd.add_argument("--destination", help="Destination folder (default: <source>/sorted-preview)")
    quick_cmd.add_argument("--max-files", type=int, default=200, help="Maximum files to process")
    quick_cmd.add_argument("--apply", action="store_true", help="Apply copy actions (default is dry-run)")
    quick_cmd.add_argument("--undo-file", default="./fma-undo.json", help="Where to save undo manifest")
    quick_cmd.add_argument("--log-file", default="./fma.log", help="Path to append operation logs")

    rollback_cmd = sub.add_parser("rollback", help="Rollback moves from an undo manifest")
    rollback_cmd.add_argument("--undo-file", default="./fma-undo.json", help="Undo manifest path")
    rollback_cmd.add_argument("--dry-run", action="store_true", help="Preview rollback actions only")
    rollback_cmd.add_argument("--log-file", default="./fma.log", help="Path to append operation logs")

    return parser


def _add_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", help="Path to JSON config file")
    p.add_argument("--source", default=".", help="Source directory (ignored when --config used)")
    p.add_argument("--destination", help="Destination directory (ignored when --config used)")
    p.add_argument("--log-file", default="./fma.log", help="Path to append operation logs")


def _log(log_file: str, message: str) -> None:
    path = Path(log_file).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"[{now}] {message}\n")
