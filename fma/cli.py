from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .config import FMAConfig, DEFAULT_RULES, load_config, write_example_config
from .organizer import apply_moves, plan_moves, rollback_from_undo, scan_directory


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
        restored = rollback_from_undo(Path(args.undo_file).expanduser().resolve())
        print(f"Rollback complete: restored {restored} files.")
        return 0

    config = _resolve_config(args)

    if args.command == "scan":
        results = scan_directory(config.source_dir, recursive=args.recursive)
        print(json.dumps([asdict(x) for x in results], indent=2))
        return 0

    if args.command == "organize":
        planned = plan_moves(
            config.source_dir,
            config.destination_dir,
            config.rules,
            recursive=args.recursive,
            mode=args.mode,
        )

        if args.dry_run:
            print(json.dumps([asdict(x) for x in planned], indent=2))
            print(f"\nDry run complete: {len(planned)} files would be moved.")
            return 0

        undo_path = Path(args.undo_file).expanduser().resolve()
        moved = apply_moves(planned, undo_file=undo_path)
        print(f"Applied {moved} moves.")
        print(f"Undo map written to: {undo_path}")
        return 0

    parser.print_help()
    return 1


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
    org_cmd.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    org_cmd.add_argument("--undo-file", default="./fma-undo.json", help="Where to save move manifest")
    org_cmd.add_argument("--recursive", action="store_true", help="Organize files recursively")
    org_cmd.add_argument("--mode", choices=["extension", "date"], default="extension", help="Organization mode")

    rollback_cmd = sub.add_parser("rollback", help="Rollback moves from an undo manifest")
    rollback_cmd.add_argument("--undo-file", default="./fma-undo.json", help="Undo manifest path")

    return parser


def _add_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", help="Path to JSON config file")
    p.add_argument("--source", default=".", help="Source directory (ignored when --config used)")
    p.add_argument("--destination", help="Destination directory (ignored when --config used)")
