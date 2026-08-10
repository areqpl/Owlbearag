# 🦉 OWLBEARAG

```text
  ____           _ _                     _     ____    _    ____ 
 / __ \         | | |                   | |   |  _ \  / \  / ___|
| |  | |_      _| | |__   ___  __ _ _ __| |__ | |_) |/ _ \| |  _ 
| |  | \ \ /\ / / | '_ \ / _ \/ _` | '__| '_ \|  _ // ___ \ |_| |
| |__| |\ V  V /| | |_) |  __/ (_| | |  | | | | | \/ /   \ \____|
 \____/  \_/\_/ |_|_.__/ \___|\__,_|_|  |_| |_|_| \_\/   \_\____|
```

> **Multi-Node AI Orchestration, PyTorch Vector Reranking & Dual-GPU Compute Management Console.**

---

[![Build Status](https://img.shields.io/github/actions/workflow/status/areqpl/Owlbearag/auto-release.yml?branch=main&style=for-the-badge&logo=github&color=purple)](https://github.com/areqpl/Owlbearag/actions)
[![Latest Release](https://img.shields.io/github/v/release/areqpl/Owlbearag?color=emerald&style=for-the-badge&logo=github)](https://github.com/areqpl/Owlbearag/releases/latest)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![PyTorch CUDA](https://img.shields.io/badge/PyTorch-CUDA_AMP-orange.svg?style=for-the-badge&logo=pytorch)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-violet.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## ⚡ What is Owlbearag?

**Owlbearag** bridges your local workstation to remote GPU accelerator nodes and Cloudflare production VPS clusters. Whether you need live dual-GPU telemetry, real-time PyTorch document reranking, or automated VPS staging synchronization, Owlbearag handles it smoothly across both a **PyQt6 Desktop GUI** and a **Rich Terminal CLI**.

---

## 🚀 Quick Start

### 1. Installation

Install directly from GitHub or download pre-built wheel binaries from [Latest Releases](https://github.com/areqpl/Owlbearag/releases/latest):

```bash
pip install git+https://github.com/areqpl/Owlbearag.git
```

### 2. Launch Interface

```bash
# Launch PyQt6 Desktop GUI
owlbearag

# Run Rich Terminal CLI
owlbearag-cli gpu status
```

---

## 🔥 Key Capabilities

- **⚡ Dual-GPU Live Telemetry**: Stream `nvidia-smi` memory allocations, core temperatures, and model states over SSH (`GTX 1080` + `RTX 3060`).
- **🧠 PyTorch Neural Vector Reranker**: Custom CUDA float16 AMP similarity matrix calculations for chunk reranking.
- **🌐 Cloudflare VPS Synchronization**: Automated background `rsync` workers pulling staging configurations from remote production nodes.
- **💬 Web Application & GitHub Pages**: Lightweight React + Vite chat UI with true AMOLED dark mode, token streaming, and native multilingual support (English, Polish, Ukrainian, Chinese, Dutch, German).
- **🔍 389+ Dynamic Command Auto-Discovery**: Auto-scans local agent skills, CLI functions, and remote SSH tools in real time.
- **🔧 Self-Healing Connection Resolver**: Probes Ollama HTTP endpoints, tests fallbacks, and executes systemd service restarts automatically.

---

## 📚 Deep Technical Documentation

- ⚡ [**PyTorch Neural Reranker Architecture**](docs/pytorch-reranker.md)
- ⚡ [**Dual-GPU Telemetry & Model Management**](docs/gpu-telemetry.md)
- 🌐 [**Cloudflare VPS Synchronization**](docs/vps-sync.md)
- 🌐 [**Dynamic Command Auto-Discovery Engine**](docs/command-discovery.md)
- 🔐 [**Configuration & Security Reference**](docs/configuration-security.md)

---

## 📜 License

Released under the **[MIT License](LICENSE)**.

> **⚠️ Windows users:** The generated `owlbearag.exe` may trigger Windows Defender SmartScreen false‑positive warnings. This is harmless; you can allow the app to run.
