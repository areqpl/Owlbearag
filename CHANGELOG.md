# Changelog

All notable changes to the **Owlbearag** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-08-09

### Added
- **PyTorch Reranker**: CUDA float16 cosine similarity matrix calculation using `torch.nn.functional.cosine_similarity()`.
- **Dual-GPU Monitoring**: `nvidia-smi` telemetry streaming over SSH (`GTX 1080` + `RTX 3060`).
- **Remote Model Management**: Pull and delete Ollama models on remote accelerator nodes over SSH.
- **Cloudflare VPS Sync**: Automated background `rsync` workers pulling staging builds from production VPS nodes.
- **Dynamic Command Discovery**: Auto-discovers 389+ commands across local skills, tools, and remote SSH nodes.
- **Self-Healing Connection Resolver**: Probes Ollama HTTP endpoints, tests fallbacks, and executes systemd service restarts automatically.
- **Automated Continuous Releases**: GitHub Actions workflow automatically builds `.whl` and `.tar.gz` and publishes a GitHub Release on every single commit pushed to `main`.
