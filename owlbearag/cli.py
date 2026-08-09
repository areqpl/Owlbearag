#!/usr/bin/env python3
"""
OWLBEARAG-CLI — IMPERIAL MULTI-NODE & DUAL-GPU REMOTE COMMAND LINE CONSOLE
Rich Colorful Markdown, Fluid Animated Status Indicators & Remote Node Hub
Commands:
  owlbearag-cli query <prompt> [--model MODEL]
  owlbearag-cli rag <search_query>
  owlbearag-cli vps [status|sync]
  owlbearag-cli hf <keyword>
  owlbearag-cli gpu [status|pull <model>|exec <cmd>]
"""

import sys
import os
import json
import sqlite3
import urllib.request
import urllib.parse
import subprocess
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status

console = Console()

HOME = Path.home()
RAG_DB_PATH = HOME / ".gemini/antigravity-cli/knowledge/rag_knowledge_base.sqlite"
SAVED_CHATS_DIR = HOME / ".gemini/antigravity-cli/saved_chats"
VPS_SYNC_DIR = HOME / ".gemini/antigravity-cli/vps_f76_sync"
CONFIG_FILE_PATH = HOME / ".gemini/antigravity-cli/config.json"

DEFAULT_OLLAMA_HOST = os.getenv("OWLBEARAG_OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_GPU_HOST = os.getenv("OWLBEARAG_GPU_HOST", "user@gpu-node.local")
DEFAULT_VPS_HOST = os.getenv("OWLBEARAG_VPS_HOST", "user@vps.example.com")

def get_config():
    if CONFIG_FILE_PATH.exists():
        try:
            return json.loads(CONFIG_FILE_PATH.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {
        "ollama_host": DEFAULT_OLLAMA_HOST,
        "remote_gpu_host": DEFAULT_GPU_HOST,
        "remote_vps_host": DEFAULT_VPS_HOST
    }

def print_banner():
    banner_text = "[bold magenta]🦉 OWLBEARAG-CLI — MULTI-NODE RAG & GPU CONSOLE[/bold magenta]\n" \
                  "[cyan]Nodes: Workstation (Local) | Remote GPU Core | Cloudflare VPS[/cyan]"
    console.print(Panel(banner_text, border_style="magenta", expand=False))

def handle_query(args):
    cfg = get_config()
    ollama_host = cfg.get("ollama_host", DEFAULT_OLLAMA_HOST)
    prompt = " ".join(args) if args else "Hello model!"
    model = "deepseek-r1-abliterated:latest"

    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]
            prompt = " ".join(args[:idx])

    console.print(f"[bold cyan]🚀 Transmitting prompt to model [{model}] at {ollama_host}...[/bold cyan]\n")
    
    with console.status("[bold green]Synthesizing response from Ollama Core...", spinner="dots"):
        try:
            url = f"{ollama_host}/api/generate"
            payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode('utf-8')
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                text = res_data.get("response", "")
        except Exception as e:
            text = f"Connection Notice: {e}. Executing via rag-llm fallback..."
            cmd = ["rag-llm", prompt, "--model", model]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            text = proc.stdout if proc.stdout else proc.stderr

    console.print(Panel(Markdown(text), title=f"💬 {model} Response", border_style="green"))

def handle_rag(args):
    query = " ".join(args) if args else "PyTorch"
    console.print(f"[bold yellow]🧠 Querying SQLite RAG Knowledge Matrix for '[cyan]{query}[/cyan]'...[/bold yellow]\n")

    if not RAG_DB_PATH.exists():
        console.print("[bold red]❌ RAG database missing. Rebuild matrix in Owlbearag GUI first.[/bold red]")
        return

    with console.status("[bold yellow]Executing FTS5 Match & Neural Ranking...", spinner="earth"):
        try:
            conn = sqlite3.connect(str(RAG_DB_PATH))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, content, filepath, category, rank
                FROM fts_chunks
                WHERE fts_chunks MATCH ?
                ORDER BY rank LIMIT 5
            """, (query,))
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            console.print(f"[bold red]RAG Query Exception: {e}[/bold red]")
            return

    if not rows:
        console.print(f"[bold red]No matching RAG matrix documents found for '{query}'.[/bold red]")
        return

    console.print(f"[bold green]Top {len(rows)} RAG Matrix Results for '{query}':[/bold green]\n")
    for idx, (title, content, filepath, category, rank) in enumerate(rows, 1):
        snippet = content[:300].replace("\n", " ") + "..."
        card_content = f"[bold cyan]Category:[/bold cyan] {category} | [bold yellow]FTS Rank:[/bold yellow] {rank:.2f}\n\n{snippet}\n\n[dim]File: {filepath}[/dim]"
        console.print(Panel(card_content, title=f"[{idx}] {title}", border_style="cyan"))

def handle_vps(args):
    cfg = get_config()
    vps_host = cfg.get("remote_vps_host", DEFAULT_VPS_HOST)
    subcmd = args[0] if args else "status"

    if subcmd == "status":
        console.print(f"[bold cyan]🌐 Querying Cloudflare F76 VPS ({vps_host}) Uptime & Disk Usage...[/bold cyan]\n")
        with console.status(f"[bold cyan]Connecting via SSH to {vps_host}...", spinner="bouncingBar"):
            cmd = ["ssh", "-o", "ConnectTimeout=5", vps_host, "uptime && df -h /"]
            proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode == 0:
            lines = proc.stdout.strip().split("\n")
            uptime_str = lines[0] if len(lines) > 0 else "Unknown"
            disk_str = lines[-1] if len(lines) > 1 else "Unknown"

            table = Table(title="🌐 Cloudflare F76 VPS Status Report", border_style="cyan")
            table.add_column("Parameter", style="bold magenta")
            table.add_column("Value", style="cyan")
            table.add_row("Host Address", vps_host)
            table.add_row("Hostname", "f76")
            table.add_row("System Uptime", uptime_str)
            table.add_row("Root Disk Usage", disk_str)
            console.print(table)
        else:
            console.print(f"[bold red]VPS SSH Exception: {proc.stderr}[/bold red]")

    elif subcmd == "sync":
        console.print(f"[bold yellow]🚀 Synchronizing F76 Project Data from Cloudflare VPS ({vps_host})...[/bold yellow]\n")
        with console.status("[bold yellow]Executing rsync file transfer...", spinner="bouncingBar"):
            cmd = [
                "rsync", "-avz", "--progress",
                "-e", "ssh -o ConnectTimeout=8",
                f"{vps_host}:~/f76.world.conf",
                f"{vps_host}:~/nexus_server.py",
                f"{vps_host}:~/cf_ufw.sh",
                str(VPS_SYNC_DIR)
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode == 0:
            console.print(Panel(f"[bold green]✅ F76 VPS Sync Complete!\nLocal Path: {VPS_SYNC_DIR}[/bold green]", border_style="green"))
        else:
            console.print(f"[bold red]rsync Notice: {proc.stderr}[/bold red]")

def handle_hf(args):
    kw = args[0] if args else "gguf"
    console.print(f"[bold gold1]🤗 Searching HuggingFace Hub for '[cyan]{kw}[/cyan]'...[/bold gold1]\n")
    with console.status("[bold gold1]Querying HuggingFace API...", spinner="bouncingBall"):
        try:
            url = f"https://huggingface.co/api/models?search={urllib.parse.quote(kw)}&limit=10"
            req = urllib.request.Request(url, headers={"User-Agent": "owlbearag-cli/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                models = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            console.print(f"[bold red]HuggingFace API Exception: {e}[/bold red]")
            return

    table = Table(title=f"🤗 HuggingFace Hub Search Results for '{kw}'", border_style="gold1")
    table.add_column("Model ID", style="bold magenta")
    table.add_column("Downloads", style="cyan", justify="right")
    table.add_column("Likes", style="yellow", justify="right")

    for m in models:
        table.add_row(m.get("id", "N/A"), f"{m.get('downloads', 0):,}", str(m.get("likes", 0)))

    console.print(table)

def handle_gpu(args):
    cfg = get_config()
    gpu_host = cfg.get("remote_gpu_host", DEFAULT_GPU_HOST)
    subcmd = args[0] if args else "status"

    if subcmd == "status":
        console.print(f"[bold magenta]⚡ Querying Remote Dual-GPU Core Metrics ({gpu_host})...[/bold magenta]\n")
        with console.status("[bold magenta]Fetching nvidia-smi telemetry via SSH...", spinner="dots"):
            cmd = ["ssh", "-o", "ConnectTimeout=5", gpu_host, "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"]
            proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode == 0:
            lines = [l.strip() for l in proc.stdout.strip().split("\n") if l.strip()]
            table = Table(title=f"⚡ Remote Dual-GPU Telemetry ({gpu_host})", border_style="magenta")
            table.add_column("Index", style="bold yellow")
            table.add_column("GPU Name", style="bold magenta")
            table.add_column("Temp", style="cyan")
            table.add_column("Util", style="green")
            table.add_row("VRAM Used / Total", style="blue")

            for l in lines:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 6:
                    table.add_row(parts[0], parts[1], f"{parts[2]}°C", f"{parts[3]}%", f"{parts[4]} / {parts[5]} MiB")
            console.print(table)
        else:
            console.print(f"[bold red]GPU SSH Exception: {proc.stderr}[/bold red]")

    elif subcmd == "pull":
        model_name = args[1] if len(args) > 1 else "deepseek-r1:7b"
        console.print(f"[bold cyan]⬇️ Pulling Ollama Model [{model_name}] on Remote GPU Host ({gpu_host})...[/bold cyan]\n")
        cmd = ["ssh", "-o", "ConnectTimeout=6", gpu_host, f"ollama pull {model_name}"]
        proc = subprocess.run(cmd)
        if proc.returncode == 0:
            console.print(f"[bold green]✅ Model {model_name} pulled successfully on remote node![/bold green]")

    elif subcmd == "exec":
        rem_cmd = " ".join(args[1:]) if len(args) > 1 else "uptime"
        console.print(f"[bold yellow]🚀 Dispatching Remote Command to {gpu_host}: '{rem_cmd}'[/bold yellow]\n")
        cmd = ["ssh", "-o", "ConnectTimeout=6", gpu_host, rem_cmd]
        proc = subprocess.run(cmd)

def main():
    print_banner()
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: owlbearag-cli [query|rag|vps|hf|gpu] <args>[/yellow]")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    if cmd == "query":
        handle_query(args)
    elif cmd == "rag":
        handle_rag(args)
    elif cmd == "vps":
        handle_vps(args)
    elif cmd == "hf":
        handle_hf(args)
    elif cmd == "gpu":
        handle_gpu(args)
    else:
        console.print(f"[bold red]Unknown command '{cmd}'. Available: query, rag, vps, hf, gpu[/bold red]")

if __name__ == "__main__":
    main()
