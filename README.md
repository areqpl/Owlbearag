# 🦉 OWLBEARAG — Enterprise Multi-Node Hybrid RAG & GPU Compute Console

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/areqpl/Owlbearag)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2B-red.svg)](https://pytorch.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-Enterprise-violet.svg)](https://pypi.org/project/PyQt6/)

**Owlbearag** is an enterprise-grade, high-availability multi-node AI control suite, PyTorch neural vector reranker, and Cloudflare VPS synchronization console. Designed for local workstation deployment, dual-GPU server orchestration (`NVIDIA RTX 3060 + GTX 1080`), and remote Cloudflare production VPS clusters.

---

## 🌟 Key Enterprise Features

- **⚡ Async Multithreading Workers & Action Confirmation**: All network requests, model inferences, and remote node commands run in dedicated background `QThread` workers. Major mutating actions (model removal, service restart, matrix rebuilding) require explicit user confirmation dialogs before execution.
- **⚡ Dual-GPU Telemetry & Model Management**: Real-time `nvidia-smi` telemetry (VRAM memory allocation, GPU temperatures, core utilization) and remote Ollama model deployment (`pull` / `rm`) over SSH.
- **🔥 PyTorch Neural Vector Reranker**: Custom PyTorch CUDA-accelerated float16 cosine similarity matrix calculation for high-precision document chunk reranking.
- **🌐 Cloudflare F76 VPS Synchronization**: Automated `rsync` background workers for pulling production project configurations and staging deployments from remote Cloudflare VPS servers.
- **🔧 Automated Self-Healing Ollama Resolver**: 3-stage automated connection resolver that detects HTTP endpoint failures, probes local fallbacks, and executes remote systemd service restarts.
- **📂 Granular RAG Matrix Indexer**: Multi-threaded indexing engine with file-by-file progress tracking for skills, prompts, chat transcripts, and system documents into SQLite FTS5 (WAL Mode).
- **🖥️ Dual Interface Options**: Ultra-sleek **PyQt6 Enterprise Desktop GUI** and colorful **Rich Terminal CLI (`owlbearag-cli`)**.
- **🔐 Secure Credential Management**: Mode `0600` owner-only encrypted configuration storage (`~/.gemini/antigravity-cli/config.json`).

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Local Workstation [owlpad Workstation]
        GUI[Owlbearag PyQt6 Enterprise Console]
        CLI[owlbearag-cli Rich Terminal]
        RAG[(SQLite FTS5 RAG Matrix - WAL Mode)]
        PYTORCH[PyTorch Neural Vector Reranker]
        THREADS[Async Multithreading ThreadPool]
    end

    subgraph Dual-GPU Accelerator Node [owlyyyrt.local]
        OLLAMA_REMOTE[Ollama LLM Core - 0.0.0.0:11434]
        GPU_1[NVIDIA RTX 3060 - 12GB VRAM]
        GPU_2[NVIDIA GTX 1080 - 8GB VRAM]
        GPU_TELEMETRY[nvidia-smi Telemetry Engine]
    end

    subgraph Cloudflare VPS Production Node [37.114.37.41]
        VPS_CONF[f76.world.conf / nexus_server.py]
        UFW[Cloudflare UFW Firewall]
        STAGING[F76WorldChat_Staging]
    end

    GUI --> THREADS
    THREADS --> RAG
    THREADS --> PYTORCH
    CLI --> RAG
    
    THREADS -- SSH / HTTP --> OLLAMA_REMOTE
    THREADS -- SSH Telemetry --> GPU_TELEMETRY
    OLLAMA_REMOTE --> GPU_1
    OLLAMA_REMOTE --> GPU_2

    THREADS -- SSH / rsync --> VPS_CONF
    THREADS -- SSH / rsync --> STAGING
```

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/areqpl/Owlbearag.git
cd Owlbearag
pip install -e .
```

### 2. Launch Desktop GUI

```bash
owlbearag
```

### 3. Launch Rich Terminal CLI

```bash
# Query Dual GPU Telemetry
owlbearag-cli gpu status

# Query RAG Knowledge Matrix
owlbearag-cli rag "PyTorch"

# Check Cloudflare VPS Status
owlbearag-cli vps status
```

---

## 🔐 Security & Configuration

All endpoints, SSH keys, and configuration options are saved securely at `~/.gemini/antigravity-cli/config.json` with owner-only `0600` permissions.

Example `config.json`:

```json
{
  "ollama_host": "http://owlyyyrt.local:11434",
  "remote_gpu_host": "owlyyy@owlyyyrt.local",
  "remote_vps_host": "owlyyy@37.114.37.41",
  "use_pytorch_reranker": true,
  "pytorch_device": "cuda"
}
```

---

## 📜 License

This project is released under the **MIT License**.
