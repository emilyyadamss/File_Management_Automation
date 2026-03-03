# File Management Automation (MVP+)

A lightweight Python CLI to scan and organize files by extension or date with safe dry-run mode.

## Features

- Scan a directory and print file metadata as JSON
- Organize files by:
  - extension rules (`--mode extension`)
  - modified date buckets (`--mode date`, e.g. `2026-03`)
- Recursive mode (`--recursive`)
- Include/exclude glob filters (`--include`, `--exclude`)
- Safety guardrails:
  - dry-run preview before changes
  - max files per run (`--max-files`)
  - hard stop when >1000 planned moves unless `--max-files` is set
- Duplicate-safe moves (`file.txt` -> `file (1).txt`)
- Undo manifest output (`fma-undo.json`) containing performed moves
- Rollback command from undo manifest
- Config-driven mode via JSON
- Basic unit tests + GitHub Actions CI
- Installable package with `fma` console script

## Quick Start

From the repo root:

```bash
python3 -m fma scan --source ./example
python3 -m fma organize --source ./example --destination ./example/sorted --dry-run
python3 -m fma organize --source ./example --destination ./example/sorted
```

Recursive + date mode:

```bash
python3 -m fma organize --source ./example --destination ./example/sorted --recursive --mode date --dry-run
```

Include/exclude + capped run:

```bash
python3 -m fma organize \
  --source ./example \
  --destination ./example/sorted \
  --include "*.py" \
  --include "*.js" \
  --exclude "*/node_modules/*" \
  --max-files 200 \
  --dry-run
```

Apply and then rollback:

```bash
python3 -m fma organize --source ./example --destination ./example/sorted --undo-file ./fma-undo.json
python3 -m fma rollback --undo-file ./fma-undo.json
```

## Install as a CLI

```bash
pip install -e .
fma --help
```

## Config File

Create a starter config:

```bash
python3 -m fma init-config --path fma-config.json
```

Run using config:

```bash
python3 -m fma scan --config fma-config.json --recursive
python3 -m fma organize --config fma-config.json --mode extension --dry-run
python3 -m fma organize --config fma-config.json --mode extension
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

## Tests

```bash
python3 -m unittest discover -s tests -v
```
