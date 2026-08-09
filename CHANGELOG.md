# 📝 Changelog

All notable changes to the **Owlbearag** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-08-09

### 🚀 Added
- **Dynamic Command Auto-Discovery Engine**: Discovers **389+ commands** dynamically across installed agent skills (`~/.agents/skills`), MCP tools, CLI subcommands, and remote GPU/VPS nodes.
- **Searchable Command Hub Table**: Interactive `QTableWidget` in GUI with instant real-time filtering, double-click auto-fill, and command execution.
- **PyTorch Deep Learning Neural Reranker**: CUDA-accelerated float16 cosine similarity matrix calculation using `torch.nn.functional.cosine_similarity()`.
- **Automated Self-Healing Ollama Connection Resolver**: 3-stage health diagnostic probing HTTP endpoints, local fallbacks, and remote systemd service restarts.
- **GitHub Actions CI/CD & Dependabot Auto-Merge**: Automated build & test workflows for Python 3.10-3.12, tag release builder, and Dependabot auto-merge pipeline.

### ⚡ Security & Performance
- **SQLite WAL Mode & Busy Timeout**: Enabled `PRAGMA journal_mode=WAL;` and `PRAGMA busy_timeout=5000;` on `rag_knowledge_base.sqlite` to prevent concurrency database locks.
- **Bounded SSH Timeouts**: Applied `ConnectTimeout=4` and `ServerAliveInterval=3` across all SSH remote workers to guarantee thread-safe anti-deadlock performance.
- **Encrypted Credential Security**: Config file `~/.gemini/antigravity-cli/config.json` enforced with strict `0600` owner-only permissions.

---

## [2.0.0] - 2026-08-09

### 🚀 Initial Enterprise Release
- Enterprise Python packaging with `pyproject.toml` and `setup.py`.
- Dual interface deployment: PyQt6 Enterprise Desktop GUI (`owlbearag`) and Rich Terminal CLI (`owlbearag-cli`).
- Remote dual-GPU telemetry (`nvidia-smi` temperature, core utilization, VRAM metrics).
- Cloudflare F76 VPS synchronization via `rsync`.
