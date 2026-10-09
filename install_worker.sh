#!/bin/bash

set -e

WORKER_DIR="/workspaces/codespaces-blank"

echo "=========================================="
echo "       WORKER INSTALLER"
echo "=========================================="

cd "$WORKER_DIR"

echo "[1/4] Checking Python..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] Python3 tidak ditemukan."
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip
fi

echo "[+] Python:"
python3 --version


echo
echo "[2/4] Creating virtual environment..."

if [ ! -d "$WORKER_DIR/venv" ]; then
    python3 -m venv "$WORKER_DIR/venv"
fi

source "$WORKER_DIR/venv/bin/activate"


echo
echo "[3/4] Installing websockets..."

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade websockets


echo
echo "[4/4] Checking websockets..."

python3 -c "import websockets; print('[+] websockets:', websockets.__version__)"


echo
echo "=========================================="
echo "       INSTALLATION COMPLETE"
echo "=========================================="

echo
echo "[*] Starting worker.py..."
echo

exec python3 -u worker.py
