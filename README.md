# File Management Automation (MVP)

A lightweight Python CLI to scan and organize files by extension with safe dry-run mode.

## Features (MVP)

- Scan a directory and print file metadata as JSON
- Organize files into category folders based on extension rules
- Dry-run mode to preview changes before applying
- Duplicate-safe moves (`file.txt` -> `file (1).txt`)
- Undo manifest output (`fma-undo.json`) containing all performed moves
- Config-driven mode via JSON

## Quick Start

From the repo root:

```bash
python -m fma scan --source ./example
python -m fma organize --source ./example --destination ./example/sorted --dry-run
python -m fma organize --source ./example --destination ./example/sorted
```

## Config File

Create a starter config:

```bash
python -m fma init-config --path fma-config.json
```

Run using config:

```bash
python -m fma scan --config fma-config.json
python -m fma organize --config fma-config.json --dry-run
python -m fma organize --config fma-config.json
```

## Default Buckets

Examples:

- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Documents: `.pdf`, `.doc`, `.docx`, `.txt`, `.md`
- Data: `.csv`, `.json`
- Archives: `.zip`, `.tar`, `.gz`
- Audio/Video: `.mp3`, `.wav`, `.mp4`, `.mov`
- Code: `.py`, `.js`, `.ts`
- Everything else goes to `other`

## Next Steps

- Add recursive scan option
- Add date-based organization mode
- Add unit tests + CI
- Add rollback command from undo manifest
