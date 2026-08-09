# Owlbearag

Owlbearag is a desktop GUI and CLI tool for managing multi-node RAG, PyTorch vector reranking, and remote GPU/VPS infrastructure. It connects a local CachyOS/Linux workstation to remote GPU nodes running Ollama and Cloudflare VPS instances.

## Quick Start

### Installation

```bash
pip install git+https://github.com/areqpl/Owlbearag.git
```

### Usage

```bash
# Launch PyQt6 desktop GUI
owlbearag

# Run CLI commands
owlbearag-cli gpu status
owlbearag-cli rag "PyTorch"
```

## Features

- **PyTorch Reranker**: Reranks SQLite FTS5 search results using PyTorch float16 cosine similarity matrix calculations.
- **Dual-GPU Monitoring**: Runs `nvidia-smi` queries over SSH to stream VRAM allocation and temperature metrics from remote nodes (`owlyyyrt.local`).
- **Remote Model Management**: Pulls and removes Ollama models on remote accelerator nodes directly from the UI or CLI.
- **Cloudflare VPS Sync**: Uses `rsync` to pull server configs and staging builds from remote VPS nodes (`37.114.37.41`).
- **Dynamic Command Discovery**: Auto-discovers commands across local agent skills, CLI subcommands, and remote system utilities.
- **Self-Healing Connection Resolver**: Probes Ollama HTTP endpoints, tests fallbacks, and executes systemd service restarts if disconnected.

## Documentation

Detailed documentation is available in the `docs/` folder:

- [PyTorch Reranker](docs/pytorch-reranker.md)
- [GPU Telemetry & Model Controls](docs/gpu-telemetry.md)
- [Cloudflare VPS Sync](docs/vps-sync.md)
- [Command Discovery Engine](docs/command-discovery.md)
- [Configuration & Security](docs/configuration-security.md)

## License

MIT License. See [LICENSE](LICENSE) for details.
