#!/usr/bin/env bash
set -euo pipefail

# Resolve project directory from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

SERVICE_NAME="webhook-distributor"
CONFIG_DIR="$HOME/.config/$SERVICE_NAME"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
ENV_FILE="$CONFIG_DIR/$SERVICE_NAME.env"
SERVICE_FILE="$SYSTEMD_USER_DIR/$SERVICE_NAME.service"

# Defaults
WEBHOOK_HOST="0.0.0.0"
WEBHOOK_PORT="3128"
UNINSTALL=false

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Install/uninstall the Webhook Distributor as a systemd user service.

Options:
  --host HOST       Set webhook host (default: 0.0.0.0)
  --port PORT       Set webhook port (default: 3128)
  --uninstall       Remove the systemd service and config
  -h, --help        Show this help message
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host) WEBHOOK_HOST="$2"; shift 2 ;;
        --port) WEBHOOK_PORT="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# --- Uninstall ---
if $UNINSTALL; then
    echo "Uninstalling $SERVICE_NAME..."
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    systemctl --user daemon-reload
    echo "Service removed. Config left at $CONFIG_DIR (delete manually if desired)."
    exit 0
fi

# --- Pre-flight checks ---
if [[ ! -f "$PROJECT_DIR/app.py" ]]; then
    echo "ERROR: app.py not found in $PROJECT_DIR"
    exit 1
fi

if [[ ! -f "$PROJECT_DIR/.venv/bin/python" ]]; then
    echo "ERROR: .venv/bin/python not found. Run 'uv sync' first to create the virtual environment."
    exit 1
fi

if ! command -v systemctl &>/dev/null; then
    echo "ERROR: systemctl not found. This script requires systemd."
    exit 1
fi

# --- Create config directory and env file ---
mkdir -p "$CONFIG_DIR"
if [[ -f "$ENV_FILE" ]]; then
    echo "Config file already exists at $ENV_FILE (preserving)"
else
    cat > "$ENV_FILE" <<ENVEOF
# Webhook Distributor configuration
# Edit and restart: systemctl --user restart $SERVICE_NAME
WEBHOOK_HOST=$WEBHOOK_HOST
WEBHOOK_PORT=$WEBHOOK_PORT
ENVEOF
    echo "Created config: $ENV_FILE"
fi

# --- Install systemd service ---
mkdir -p "$SYSTEMD_USER_DIR"
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/$SERVICE_NAME.service" > "$SERVICE_FILE"
echo "Installed service: $SERVICE_FILE"

# --- Enable and start ---
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"

# --- Enable linger so service survives logout ---
if command -v loginctl &>/dev/null; then
    loginctl enable-linger "$(whoami)" 2>/dev/null || true
fi

echo ""
echo "=== $SERVICE_NAME installed ==="
echo ""
echo "Management commands:"
echo "  systemctl --user status $SERVICE_NAME    # check status"
echo "  systemctl --user restart $SERVICE_NAME   # restart"
echo "  systemctl --user stop $SERVICE_NAME      # stop"
echo "  journalctl --user -u $SERVICE_NAME -f    # follow logs"
echo ""
echo "Config: $ENV_FILE"
echo "Edit config then: systemctl --user restart $SERVICE_NAME"
