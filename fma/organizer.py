from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass
class PlannedMove:
    source: str
    destination: str
    reason: str


@dataclass
class ScanEntry:
    path: str
    size_bytes: int
    extension: str
    modified_utc: str


def scan_directory(source_dir: Path, recursive: bool = False) -> List[ScanEntry]:
    entries: List[ScanEntry] = []
    files = source_dir.rglob("*") if recursive else source_dir.iterdir()

    for item in files:
        if not item.is_file():
            continue
        stat = item.stat()
        entries.append(
            ScanEntry(
                path=str(item),
                size_bytes=stat.st_size,
                extension=item.suffix.lower(),
                modified_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            )
        )
    return entries


def plan_moves(
    source_dir: Path,
    destination_dir: Path,
    rules: Dict[str, str],
    recursive: bool = False,
    mode: str = "extension",
) -> List[PlannedMove]:
    planned: List[PlannedMove] = []
    files = source_dir.rglob("*") if recursive else source_dir.iterdir()

    for item in files:
        if not item.is_file():
            continue

        if destination_dir in item.parents:
            continue

        ext = item.suffix.lower()

        if mode == "date":
            dt = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
            bucket = f"{dt.year:04d}-{dt.month:02d}"
            reason = f"modified date -> {bucket}"
        else:
            bucket = rules.get(ext, "other")
            reason = f"extension '{ext or '[none]'}' -> {bucket}"

        destination_folder = destination_dir / bucket
        target = _dedupe_target(destination_folder / item.name)
        planned.append(PlannedMove(source=str(item), destination=str(target), reason=reason))

    return planned


def apply_moves(planned_moves: Iterable[PlannedMove], undo_file: Path) -> int:
    performed: List[dict] = []

    for move in planned_moves:
        src = Path(move.source)
        dst = Path(move.destination)

        if not src.exists():
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        performed.append(asdict(move))

    undo_file.parent.mkdir(parents=True, exist_ok=True)
    undo_file.write_text(
        json.dumps(
            {
                "created_utc": datetime.now(tz=timezone.utc).isoformat(),
                "moves": performed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return len(performed)


def rollback_from_undo(undo_file: Path) -> int:
    payload = json.loads(undo_file.read_text(encoding="utf-8"))
    moves = payload.get("moves", [])

    restored = 0
    for move in reversed(moves):
        src = Path(move["destination"])  # current location
        dst = Path(move["source"])  # original location

        if not src.exists():
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        restored += 1

    return restored


def _dedupe_target(target: Path) -> Path:
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    parent = target.parent

    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
