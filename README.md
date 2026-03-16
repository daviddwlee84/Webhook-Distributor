# Webhook Distributor

Can be used as sort of a proxy that can pass a webhook to multiple webhook hosts
Receive HTTP request and call HTTPS servers like Discord Webhook

## Getting Started

1. Add Discord webhooks to `webhooks.txt` 
2. Install dependencies `pip install -r requirements.txt`
3. Start server `docker compose up --build` (Run without docker `python app.py`)
4. (optional) test with `python debug.py` in a separate terminal

## CLI Usage

```bash
# Default: reads webhooks.txt
python app.py

# Pass webhook URLs directly (ignores webhooks.txt)
python app.py --webhooks https://url1 https://url2

# Custom host/port
python app.py --host 127.0.0.1 --port 8080 --webhooks https://url1
```

## systemd User Service

For persistent deployment on Linux:

```bash
# Install dependencies first
uv sync

# Install and start the service
./setup-systemd.sh

# With custom host/port
./setup-systemd.sh --host 127.0.0.1 --port 3128

# Management
systemctl --user status webhook-distributor
systemctl --user restart webhook-distributor
journalctl --user -u webhook-distributor -f

# Uninstall
./setup-systemd.sh --uninstall
```

Config file: `~/.config/webhook-distributor/webhook-distributor.env`

## Note

- [python - Proxying to another web service with Flask - Stack Overflow](https://stackoverflow.com/questions/6656363/proxying-to-another-web-service-with-flask)

## Trouble Shooting

- [angular5 - Problems with flask and bad request - Stack Overflow](https://stackoverflow.com/questions/49389535/problems-with-flask-and-bad-request)
  - HTTPS issue
