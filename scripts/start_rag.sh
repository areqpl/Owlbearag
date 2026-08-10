#!/usr/bin/env bash
set -e

# This script starts the Owlbearag RAG FastAPI server via systemd and then launches the GUI client.
# It is intended to be used on the local user session (e.g., from autostart or manual execution).

# Ensure the systemd user services are loaded
systemctl --user daemon-reload || true

# Start (or restart) the FastAPI server service
systemctl --user restart owlbearag_server.service

# Give the server a moment to start up
sleep 2

# Launch the GUI client in the background (non‑blocking)
# Using 'nohup' ensures the process stays alive after the script exits.
nohup python3 /home/owlyyy/Projects/Owlbearag/llama_node/gui_client.py >/dev/null 2>&1 &

echo "Owlbearag RAG server started and GUI client launched."
