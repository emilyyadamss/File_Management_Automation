from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

DEFAULT_RULES: Dict[str, str] = {
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".gif": "images",
    ".webp": "images",
    ".pdf": "documents",
    ".doc": "documents",
    ".docx": "documents",
    ".txt": "documents",
    ".md": "documents",
    ".csv": "data",
    ".json": "data",
    ".zip": "archives",
    ".tar": "archives",
    ".gz": "archives",
    ".mp3": "audio",
    ".wav": "audio",
    ".mp4": "video",
    ".mov": "video",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
}


@dataclass
class FMAConfig:
    source_dir: Path
    destination_dir: Path
    rules: Dict[str, str]


def load_config(config_path: Path) -> FMAConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))

    source_dir = Path(data.get("source_dir", ".")).expanduser().resolve()
    destination_dir = Path(data.get("destination_dir", source_dir)).expanduser().resolve()

    rules = {k.lower(): v for k, v in data.get("rules", DEFAULT_RULES).items()}
    return FMAConfig(source_dir=source_dir, destination_dir=destination_dir, rules=rules)


def write_example_config(path: Path) -> None:
    payload = {
        "source_dir": "./downloads",
        "destination_dir": "./downloads/sorted",
        "rules": DEFAULT_RULES,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
