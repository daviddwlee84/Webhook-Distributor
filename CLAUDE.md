# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Webhook Distributor is a Flask-based HTTP proxy that receives a single webhook request and fans it out to multiple destination URLs (e.g., Discord webhooks). Destinations are listed in `webhooks.txt`, one URL per line.

## Commands

```bash
# Install dependencies (using uv)
uv sync

# Run locally
python app.py                          # default: 0.0.0.0:3128
python app.py --host 127.0.0.1 --port 8080  # custom host/port (via tyro CLI)

# Run with Docker
docker compose up --build              # serves on port 3128

# Test manually
python debug.py                        # sends a test Discord webhook to localhost:3128
```

```bash
# Run with systemd (user service)
./setup-systemd.sh                     # install & start service
./setup-systemd.sh --host 127.0.0.1 --port 8080  # custom host/port
./setup-systemd.sh --uninstall         # remove service
systemctl --user status webhook-distributor
journalctl --user -u webhook-distributor -f
```

## Architecture

- **`app.py`** — Single-file Flask app. Proxies all incoming GET/POST requests to every configured webhook destination. Returns a JSON dict of `{host: status_code}`. CLI args (`--host`, `--port`, `--webhooks`) handled by `tyro`. Uses `loguru` for structured logging.
- **`webhooks.txt`** — One webhook URL per line. Optional if `--webhooks` CLI args are provided.
- **`debug.py`** — Sends a test payload via `discord_webhook` pointed at the local server.
- **`Dockerfile`** — Uses `flask run` (Python 3.8 slim). The `docker-compose.yml` mounts the project directory and exposes port 3128.

## Key Details

- The proxy strips hop-by-hop headers (`content-encoding`, `content-length`, `transfer-encoding`, `connection`) from upstream responses per RFC 2616 §13.5.1.
- Webhook URLs can be provided via `--webhooks` CLI args (takes priority) or `webhooks.txt` file (fallback). The server must be restarted to pick up changes.
- Both `requirements.txt` (pip) and `pyproject.toml` (uv) exist; `pyproject.toml` is the more current dependency spec (Python ≥3.13, includes `tyro` and `loguru`).
- `setup-systemd.sh` installs a systemd user service with auto-restart on failure (5s delay, max 5 restarts per 5 min). Config lives at `~/.config/webhook-distributor/webhook-distributor.env`.
