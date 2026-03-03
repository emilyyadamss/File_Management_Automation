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


def scan_directory(source_dir: Path) -> List[ScanEntry]:
    entries: List[ScanEntry] = []
    for item in source_dir.iterdir():
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


def plan_moves(source_dir: Path, destination_dir: Path, rules: Dict[str, str]) -> List[PlannedMove]:
    planned: List[PlannedMove] = []

    for item in source_dir.iterdir():
        if not item.is_file():
            continue

        ext = item.suffix.lower()
        bucket = rules.get(ext, "other")
        destination_folder = destination_dir / bucket
        target = _dedupe_target(destination_folder / item.name)

        planned.append(
            PlannedMove(source=str(item), destination=str(target), reason=f"extension '{ext or '[none]'}' -> {bucket}")
        )

    return planned


def apply_moves(planned_moves: Iterable[PlannedMove], undo_file: Path) -> int:
    performed: List[dict] = []

    for move in planned_moves:
        src = Path(move.source)
        dst = Path(move.destination)

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
