# ⚡ Dual-GPU Telemetry & Model Management

## Overview
Owlbearag monitors remote dual-GPU accelerator nodes over SSH without blocking the main event thread.

## Supported Telemetry Metrics
- **VRAM Allocation**: Displays used vs total video memory for each GPU (e.g. `GTX 1080: 11/8192 MiB` & `RTX 3060: 304/12288 MiB`).
- **Core Temperatures**: Live GPU core temperatures (in °C).
- **Remote Model Management**: Pull (`ollama pull`) or remove (`ollama rm`) remote Ollama models.
