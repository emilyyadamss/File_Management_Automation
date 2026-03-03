# File Management Automation (MVP+)

A lightweight Python CLI to scan and organize files by extension or date with safe dry-run mode.

## Features

- Scan a directory and print file metadata as JSON
- Organize files by:
  - extension rules (`--mode extension`)
  - modified date buckets (`--mode date`, e.g. `2026-03`)
- Recursive mode (`--recursive`)
- Include/exclude glob filters (`--include`, `--exclude`)
- Choose operation mode:
  - move files (default)
  - copy files (`--operation copy`)
- Safety guardrails:
  - dry-run preview before changes
  - max files per run (`--max-files`)
  - hard stop when >1000 planned moves unless `--max-files` is set
- Undo manifest output (`fma-undo.json`) containing performed actions
- Rollback command from undo manifest, including rollback dry-run
- Operation logging (`--log-file`, default `./fma.log`)
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

Copy mode (non-destructive):

```bash
python3 -m fma organize --source ./example --destination ./example/sorted --operation copy --dry-run
python3 -m fma organize --source ./example --destination ./example/sorted --operation copy
```

Apply and then rollback:

```bash
python3 -m fma organize --source ./example --destination ./example/sorted --undo-file ./fma-undo.json
python3 -m fma rollback --undo-file ./fma-undo.json --dry-run
python3 -m fma rollback --undo-file ./fma-undo.json
```

Use a custom log file:

```bash
python3 -m fma organize --source ./example --destination ./example/sorted --log-file ./logs/fma.log
```

Quick preset for coding repositories (dry-run by default):

```bash
python3 -m fma quick-project --source ~/projects/Weather
python3 -m fma quick-project --source ~/projects/Weather --apply
```

The `quick-project` preset automatically:
- uses recursive scan
- includes code files (`*.py`, `*.js`, `*.ts`, `*.tsx`, `*.jsx`)
- excludes common build folders (`.git`, `node_modules`, `.next`, `dist`, `build`, `coverage`, virtual envs)
- runs as copy mode with max-files cap

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

## Tests

```bash
python3 -m unittest discover -s tests -v
```
