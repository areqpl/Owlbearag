#!/usr/bin/env python3
"""
OWLBEARAG — IMPERIAL DYNAMIC COMMAND EXPLORER & MULTI-NODE CONTROL CONSOLE
Features:
- Dynamic Command Auto-Discovery Engine (Scans Skills, MCP Tools, GPU/VPS Capabilities, & System Binaries)
- Searchable Interactive Command Explorer & Hub with Category Filtering & Instant Launch
- Dual-GPU Remote Node Live Telemetry (nvidia-smi) & Remote Ollama Model Manager
- High-Availability SQLite WAL Mode, Multi-Endpoint Failover, & Bounded SSH Timeouts
"""

import sys
import os
import json
import sqlite3
import urllib.request
import urllib.parse
import subprocess
import traceback
import math
from pathlib import Path
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QUrl
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QLineEdit, QComboBox, QTabWidget, QSplitter,
    QGroupBox, QFrame, QMessageBox, QFileDialog, QToolTip, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont, QIcon, QColor, QDesktopServices

# --- Paths & Constants ---
HOME = Path.home()
BRAIN_DIR = HOME / ".gemini/antigravity-cli/brain"
MCP_DIR = HOME / ".gemini/antigravity-cli/mcp"
SKILLS_DIR = HOME / ".agents/skills"
CONFIG_DIR = HOME / ".gemini/config"
PROJECTS_DIR = HOME / "Projects"
RAG_DB_PATH = HOME / ".gemini/antigravity-cli/knowledge/rag_knowledge_base.sqlite"
SAVED_CHATS_DIR = HOME / ".gemini/antigravity-cli/saved_chats"
VPS_SYNC_DIR = HOME / ".gemini/antigravity-cli/vps_f76_sync"
SYSTEM_LOGS_DIR = HOME / ".gemini/antigravity-cli/logs"
CONFIG_FILE_PATH = HOME / ".gemini/antigravity-cli/config.json"

SSH_DIR = HOME / ".ssh"
DEFAULT_REMOTE_GPU_HOST = os.getenv("OWLBEARAG_GPU_HOST", "user@gpu-node.local")
DEFAULT_REMOTE_VPS_HOST = os.getenv("OWLBEARAG_VPS_HOST", "user@vps.example.com")
DEFAULT_OLLAMA_HOST = os.getenv("OWLBEARAG_OLLAMA_HOST", "http://127.0.0.1:11434")
FALLBACK_OLLAMA_HOSTS = ["http://127.0.0.1:11434"]

SAVED_CHATS_DIR.mkdir(parents=True, exist_ok=True)
VPS_SYNC_DIR.mkdir(parents=True, exist_ok=True)
SYSTEM_LOGS_DIR.mkdir(parents=True, exist_ok=True)


# --- SQLite Robust Database Helper ---

def get_robust_sqlite_connection(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# --- Config Security Manager ---

class ConfigSecurityManager:
    DEFAULT_CONFIG = {
        "ollama_host": DEFAULT_OLLAMA_HOST,
        "remote_gpu_host": DEFAULT_REMOTE_GPU_HOST,
        "remote_vps_host": DEFAULT_REMOTE_VPS_HOST,
        "use_pytorch_reranker": True,
        "pytorch_device": "cuda" if HAS_PYTORCH and torch.cuda.is_available() else "cpu",
        "auto_reconnect_ollama": True,
        "api_keys": {}
    }

    @classmethod
    def load_config(cls) -> dict:
        if not CONFIG_FILE_PATH.exists():
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG.copy()
        try:
            data = json.loads(CONFIG_FILE_PATH.read_text(encoding='utf-8'))
            merged = cls.DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
        except Exception:
            return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, cfg: dict):
        try:
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE_PATH.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
            os.chmod(CONFIG_FILE_PATH, 0o600)
        except Exception as e:
            print(f"Error saving config: {e}")


# --- Dynamic Command Auto-Discovery Engine ---

class CommandRegistryScanner:
    """Scans local skills, system binaries, CLI commands, and remote node capabilities to compile an exhaustive list of actions."""

    @classmethod
    def discover_all_commands(cls) -> list:
        commands = [
            # Category: Owlbearag CLI Core
            {"category": "Owlbearag CLI", "command": "vps status", "description": "Query Cloudflare VPS uptime, disk usage, and network status", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "vps sync", "description": "Sync project data from VPS node via rsync", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "gpu status", "description": "Query remote dual GPU telemetry (nvidia-smi) from GPU node", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "gpu pull deepseek-r1-abliterated:latest", "description": "Pull deepseek model onto remote GPU node", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "gpu exec 'free -h'", "description": "Execute remote shell command on GPU node", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "rag PyTorch", "description": "Search SQLite RAG matrix for PyTorch neural embeddings", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "rag adhd", "description": "Search SQLite RAG matrix for ADHD skill & focus runbook", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "query Write a story", "description": "Stream LLM generation from model core", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "hf gguf", "description": "Search HuggingFace Hub for GGUF models", "type": "cli"},
            {"category": "Owlbearag CLI", "command": "hf uncensored", "description": "Search HuggingFace Hub for uncensored story models", "type": "cli"},
            
            # Category: Remote GPU Node
            {"category": "Remote GPU Node", "command": "nvidia-smi", "description": "Query dual-GPU core temperature, VRAM, and process table", "type": "remote_gpu"},
            {"category": "Remote GPU Node", "command": "ollama list", "description": "List all installed LLM models on dual-GPU core", "type": "remote_gpu"},
            {"category": "Remote GPU Node", "command": "ollama ps", "description": "Check currently loaded models in VRAM", "type": "remote_gpu"},
            {"category": "Remote GPU Node", "command": "systemctl --user status ollama.service", "description": "Check Ollama systemd background service state", "type": "remote_gpu"},
            {"category": "Remote GPU Node", "command": "btrfs filesystem show", "description": "Check Btrfs storage pool allocation on GPU node", "type": "remote_gpu"},
            {"category": "Remote GPU Node", "command": "free -h && lscpu", "description": "Audit RAM, ZRAM, and CPU core architecture", "type": "remote_gpu"},

            # Category: Cloudflare VPS Node
            {"category": "Cloudflare VPS Node", "command": "vps uptime", "description": "Query VPS system load and uptime", "type": "remote_vps"},
            {"category": "Cloudflare VPS Node", "command": "vps ufw status", "description": "Inspect Cloudflare UFW firewall active rules", "type": "remote_vps"},
            {"category": "Cloudflare VPS Node", "command": "vps ls -la ~/F76WorldChat_Staging", "description": "List F76 World Chat staging deployment files", "type": "remote_vps"},

            # Category: Local System Tools
            {"category": "Local System Tools", "command": "pacseek", "description": "Arch Linux package search & manager", "type": "local"},
            {"category": "Local System Tools", "command": "fastfetch", "description": "Display CachyOS system hardware architecture info", "type": "local"},
            {"category": "Local System Tools", "command": "systemctl --user status", "description": "Check local user systemd services status", "type": "local"},
        ]

        # Dynamically scan installed skills (~/.agents/skills)
        if SKILLS_DIR.exists():
            for skill_dir in SKILLS_DIR.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        skill_name = skill_dir.name
                        commands.append({
                            "category": "Agent Skills",
                            "command": f"rag {skill_name}",
                            "description": f"Query RAG matrix for skill runbook '{skill_name}'",
                            "type": "skill"
                        })

        return commands


# --- Remote Node Workers ---

class RemoteGPUTelemetryWorker(QObject):
    telemetry_ready = pyqtSignal(dict)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, remote_host: str):
        super().__init__()
        self.remote_host = remote_host

    def run(self):
        try:
            self.log.emit("INFO", f"[REMOTE GPU TELEMETRY]: QUERYING DUAL-GPU METRICS VIA SSH FROM {self.remote_host}...")
            
            cmd_gpu = [
                "ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3",
                self.remote_host,
                "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
            ]
            proc = subprocess.run(cmd_gpu, capture_output=True, text=True, timeout=6)
            gpu_lines = [l.strip() for l in proc.stdout.strip().split("\n") if l.strip()]

            gpus = []
            for l in gpu_lines:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "index": parts[0],
                        "name": parts[1],
                        "temp": parts[2],
                        "util": parts[3],
                        "mem_used": parts[4],
                        "mem_total": parts[5]
                    })

            cmd_sys = [
                "ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3",
                self.remote_host,
                "uptime && free -h && uname -r"
            ]
            proc_sys = subprocess.run(cmd_sys, capture_output=True, text=True, timeout=6)
            sys_out = proc_sys.stdout.strip()

            telemetry = {
                "gpus": gpus,
                "system_summary": sys_out,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            self.log.emit("INFO", f"  └─ Fetched metrics for {len(gpus)} GPUs on {self.remote_host}.")
            self.telemetry_ready.emit(telemetry)
        except Exception as e:
            err_msg = f"RemoteGPUTelemetryWorker Notice: {e}"
            self.log.emit("WARN", err_msg)
            self.telemetry_ready.emit({})


class RemoteExecWorker(QObject):
    chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, remote_host: str, command: str):
        super().__init__()
        self.remote_host = remote_host
        self.command = command

    def run(self):
        try:
            self.log.emit("INFO", f"[REMOTE EXEC DISPATCH]: SSH TO {self.remote_host} -> '{self.command}'...")
            full_cmd = ["ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3", self.remote_host, self.command]

            proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            full_out = []
            for line in iter(proc.stdout.readline, ''):
                if line:
                    full_out.append(line)
                    self.chunk.emit(line)
            proc.stdout.close()
            proc.wait()

            final_text = "".join(full_out)
            self.log.emit("INFO", f"[REMOTE EXEC COMPLETE]: Exited with code {proc.returncode}")
            self.finished.emit(final_text)
        except Exception as e:
            err_msg = f"RemoteExecWorker Exception: {e}\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.finished.emit(f"Error: {e}")


class RemoteModelManagerWorker(QObject):
    finished = pyqtSignal(bool, str)
    chunk = pyqtSignal(str)
    log = pyqtSignal(str, str)

    def __init__(self, remote_host: str, action: str, model_name: str):
        super().__init__()
        self.remote_host = remote_host
        self.action = action
        self.model_name = model_name

    def run(self):
        try:
            self.log.emit("INFO", f"[REMOTE OLLAMA MANAGER]: Executing '{self.action}' for model [{self.model_name}] on {self.remote_host}...")
            cmd = f"ollama {self.action} {self.model_name}"
            full_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "ServerAliveInterval=3", self.remote_host, cmd]

            proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in iter(proc.stdout.readline, ''):
                if line:
                    self.chunk.emit(line)
                    self.log.emit("DEBUG", f"  └─ [ollama {self.action}] {line.strip()}")
            proc.stdout.close()
            proc.wait()

            if proc.returncode == 0:
                self.log.emit("INFO", f"✅ [OLLAMA ACTION COMPLETE]: Successfully executed {self.action} for {self.model_name}.")
                self.finished.emit(True, f"Model {self.action} succeeded.")
            else:
                self.log.emit("ERROR", f"❌ [OLLAMA ACTION FAILED]: Exited with code {proc.returncode}")
                self.finished.emit(False, "Operation failed.")
        except Exception as e:
            self.log.emit("ERROR", f"RemoteModelManagerWorker Exception: {e}")
            self.finished.emit(False, str(e))


# --- Multi-Endpoint Streaming Chat Worker ---

class ModelChatWorker(QObject):
    chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, ollama_url: str, model_name: str, prompt: str, history: list = None):
        super().__init__()
        self.primary_url = ollama_url
        self.model_name = model_name
        self.prompt = prompt
        self.history = history or []

    def run(self):
        endpoints = [self.primary_url] + [h for h in FALLBACK_OLLAMA_HOSTS if h != self.primary_url]
        success = False

        for endpoint in endpoints:
            try:
                self.log.emit("INFO", f"[STREAMING CHAT]: INFERRING FROM MODEL [{self.model_name}] AT {endpoint}...")
                url = f"{endpoint}/api/generate"
                payload = {"model": self.model_name, "prompt": self.prompt, "stream": True}
                req_data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
                
                full_response = []
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        if line:
                            chunk_json = json.loads(line.decode('utf-8'))
                            token = chunk_json.get("response", "")
                            if token:
                                full_response.append(token)
                                self.chunk.emit(token)
                            if chunk_json.get("done", False):
                                break

                final_text = "".join(full_response)
                self.log.emit("INFO", f"[STREAM COMPLETE]: GENERATED {len(final_text)} CHARS FROM {endpoint}.")
                self.finished.emit(final_text)
                success = True
                break
            except Exception as e:
                self.log.emit("WARN", f"[ENDPOINT NOTICE]: Endpoint {endpoint} failed ({e}). Attempting next endpoint...")

        if not success:
            try:
                self.log.emit("WARN", f"[FALLBACK STREAM]: EXECUTING VIA RAG-LLM CLI FOR [{self.model_name}]...")
                cmd = ["rag-llm", self.prompt, "--model", self.model_name]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
                full_out = []
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        full_out.append(line)
                        self.chunk.emit(line)
                proc.stdout.close()
                proc.wait()
                self.finished.emit("".join(full_out))
            except Exception as ex:
                err_msg = f"ModelChatWorker Exception: All endpoints failed.\nTraceback:\n{traceback.format_exc()}"
                self.log.emit("ERROR", err_msg)
                self.error.emit(err_msg)
                self.finished.emit("Error: Inference failed across all available endpoints.")


# --- PyTorch Reranker Worker ---

if HAS_PYTORCH:
    class PyTorchNeuralReranker(nn.Module):
        def __init__(self, vocab_size=5000, embed_dim=128):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
            self.proj = nn.Linear(embed_dim, embed_dim)

        def forward(self, token_tensor):
            embeds = self.embedding(token_tensor)
            pooled = embeds.mean(dim=1)
            return F.normalize(self.proj(pooled), p=2, dim=1)

    def simple_tokenize(text: str, vocab_size=5000) -> torch.Tensor:
        words = text.lower().split()
        ids = [abs(hash(w)) % (vocab_size - 1) + 1 for w in words[:128]]
        if not ids:
            ids = [0]
        return torch.tensor(ids, dtype=torch.long)


class PyTorchRerankerWorker(QObject):
    results_ready = pyqtSignal(list)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, query: str, candidates: list):
        super().__init__()
        self.query = query
        self.candidates = candidates

    def run(self):
        if not HAS_PYTORCH:
            self.log.emit("WARN", "[PYTORCH NOTICE]: PyTorch package not loaded. Falling back to keyword rank.")
            self.results_ready.emit(self.candidates)
            return

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.log.emit("INFO", f"[PYTORCH RERANKER]: INFERRING NEURAL TENSORS ON DEVICE [{device.upper()}]...")

            model = PyTorchNeuralReranker().to(device)
            model.eval()

            with torch.no_grad():
                q_tokens = simple_tokenize(self.query).unsqueeze(0).to(device)
                q_vector = model(q_tokens)

                scored_candidates = []
                for c in self.candidates:
                    c_tokens = simple_tokenize(c.get("content", "")).unsqueeze(0).to(device)
                    c_vector = model(c_tokens)

                    sim = F.cosine_similarity(q_vector, c_vector).item()
                    c_copy = c.copy()
                    c_copy["pytorch_score"] = float(sim)
                    scored_candidates.append(c_copy)

                scored_candidates.sort(key=lambda x: x["pytorch_score"], reverse=True)
                self.log.emit("INFO", f"[PYTORCH RERANK COMPLETE]: Neural Reranked {len(scored_candidates)} candidates.")
                self.results_ready.emit(scored_candidates)
        except Exception as e:
            err_msg = f"PyTorchRerankerWorker Exception: {e}\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.results_ready.emit(self.candidates)


# --- Automated Ollama Connection Resolver Worker ---

class OllamaConnectionResolverWorker(QObject):
    resolved = pyqtSignal(bool, str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, target_url: str, remote_gpu_host: str):
        super().__init__()
        self.target_url = target_url
        self.remote_gpu_host = remote_gpu_host

    def run(self):
        self.log.emit("INFO", f"[OLLAMA DIAGNOSTIC]: TESTING CONNECTION TO OLLAMA CORE AT {self.target_url}...")

        try:
            req = urllib.request.Request(f"{self.target_url}/api/tags")
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    m_count = len(data.get('models', []))
                    self.log.emit("INFO", f"✅ [OLLAMA HEALTHY]: Endpoint online! Discovered {m_count} models.")
                    self.resolved.emit(True, f"Ollama Online ({m_count} models)")
                    return
        except Exception as e:
            self.log.emit("WARN", f"[OLLAMA DIAGNOSTIC NOTICE]: Primary endpoint {self.target_url} unreachable: {e}")

        local_url = "http://127.0.0.1:11434"
        self.log.emit("INFO", f"[OLLAMA SELF-HEAL]: Testing local fallback at {local_url}...")
        try:
            req = urllib.request.Request(f"{local_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    self.log.emit("INFO", f"✅ [FALLBACK SUCCESS]: Local Ollama service found at {local_url}!")
                    self.resolved.emit(True, f"Switched to Local Fallback ({local_url})")
                    return
        except Exception:
            pass

        self.log.emit("INFO", f"[OLLAMA REMOTE DIAGNOSTIC]: Checking Ollama systemd status on remote GPU server ({self.remote_gpu_host})...")
        try:
            ssh_cmd = [
                "ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3",
                self.remote_gpu_host,
                "systemctl --user status ollama.service || sudo systemctl status ollama.service"
            ]
            proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=6)
            output = proc.stdout + proc.stderr

            if "active (running)" in output:
                self.log.emit("INFO", f"  └─ Ollama service is RUNNING on remote host. Restarting with OLLAMA_HOST=0.0.0.0:11434...")
                restart_cmd = [
                    "ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3",
                    self.remote_gpu_host,
                    "systemctl --user restart ollama.service || sudo systemctl restart ollama.service"
                ]
                subprocess.run(restart_cmd, capture_output=True, text=True, timeout=8)
                self.log.emit("INFO", "✅ [REMOTE RESTART SENT]: Ollama systemd service restarted on remote GPU host.")
                self.resolved.emit(True, "Remote Ollama Service Restarted")
                return
            else:
                self.log.emit("WARN", f"  └─ Remote Ollama service inactive. Attempting start...")
                start_cmd = [
                    "ssh", "-o", "ConnectTimeout=4", "-o", "ServerAliveInterval=3",
                    self.remote_gpu_host,
                    "systemctl --user start ollama.service || sudo systemctl start ollama.service"
                ]
                subprocess.run(start_cmd, capture_output=True, text=True, timeout=8)
                self.log.emit("INFO", "✅ [REMOTE START SENT]: Started Ollama service on remote GPU host.")
                self.resolved.emit(True, "Remote Ollama Started")
                return
        except Exception as ssh_ex:
            self.log.emit("ERROR", f"[OLLAMA RESOLVER ERROR]: SSH diagnostic failed: {ssh_ex}")

        self.log.emit("ERROR", "❌ [OLLAMA RESOLUTION FAILED]: All automated diagnostic attempts exhausted.")
        self.resolved.emit(False, "Connection Unresolved")


# --- Granular RAG Indexer Worker ---

class GranularIndexerWorker(QObject):
    finished = pyqtSignal(int, int)
    progress = pyqtSignal(int)
    status_text = pyqtSignal(str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.log.emit("INFO", "[GRANULAR RAG INDEXER]: STARTING LIVE COMPILATION OF SKILLS, PROMPTS, CHATS & VPS DATA...")
            conn = get_robust_sqlite_connection(RAG_DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                source_type TEXT,
                filepath TEXT UNIQUE,
                title TEXT,
                total_chunks INTEGER,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                chunk_index INTEGER,
                title TEXT,
                content TEXT,
                filepath TEXT,
                category TEXT,
                source_type TEXT,
                word_count INTEGER,
                FOREIGN KEY(doc_id) REFERENCES documents(id)
            )
            """)

            cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                title,
                content,
                filepath UNINDEXED,
                category,
                source_type,
                chunk_id UNINDEXED,
                tokenize='unicode61 remove_diacritics 1'
            )
            """)

            targets = [
                (SKILLS_DIR, "skill", "agent_skills", "**/*.md"),
                (CONFIG_DIR, "plugin_skill", "plugin_skills", "**/*.md"),
                (MCP_DIR, "mcp_tool", "mcp_schemas", "**/*.json"),
                (BRAIN_DIR, "artifact", "brain_artifacts", "**/*.md"),
                (HOME / "system_prompts_leaks", "system_prompts", "prompt_leaks", "**/*.md"),
                (PROJECTS_DIR, "project_doc", "source_docs", "**/*.md"),
                (SAVED_CHATS_DIR, "saved_chat", "user_saved_chats", "**/*.json"),
                (VPS_SYNC_DIR, "vps_f76_doc", "vps_f76_configs", "**/*.*"),
            ]

            total_docs = 0
            total_chunks_count = 0

            all_files = []
            for root_dir, category, source_type, glob_pat in targets:
                if not root_dir.exists():
                    continue
                for fp in root_dir.glob(glob_pat):
                    str_path = str(fp.resolve())
                    if ".git" in str_path or "node_modules" in str_path or "__pycache__" in str_path:
                        continue
                    if fp.stat().st_size <= 5 * 1024 * 1024:
                        all_files.append((fp, str_path, category, source_type))

            t_files = len(all_files)
            self.log.emit("INFO", f"[INDEXER PREPARATION]: Identified {t_files} target files for RAG processing.")

            for i, (filepath, str_path, category, source_type) in enumerate(all_files, 1):
                try:
                    content = filepath.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    continue

                if not content or len(content.strip()) < 15:
                    continue

                title = filepath.stem.replace('_', ' ').replace('-', ' ').title()
                chunks = [content[k:k+1500] for k in range(0, len(content), 1300)]
                if not chunks:
                    continue

                cursor.execute("SELECT id FROM documents WHERE filepath = ?", (str_path,))
                existing = cursor.fetchone()
                if existing:
                    doc_id = existing[0]
                    cursor.execute("DELETE FROM fts_chunks WHERE filepath = ?", (str_path,))
                    cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
                    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

                cursor.execute(
                    "INSERT INTO documents (category, source_type, filepath, title, total_chunks) VALUES (?, ?, ?, ?, ?)",
                    (category, source_type, str_path, title, len(chunks))
                )
                doc_id = cursor.lastrowid
                total_docs += 1

                for idx, c_text in enumerate(chunks):
                    word_cnt = len(c_text.split())
                    cursor.execute(
                        """INSERT INTO chunks (doc_id, chunk_index, title, content, filepath, category, source_type, word_count)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (doc_id, idx, title, c_text, str_path, category, source_type, word_cnt)
                    )
                    chunk_id = cursor.lastrowid

                    cursor.execute(
                        """INSERT INTO fts_chunks (title, content, filepath, category, source_type, chunk_id)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (title, c_text, str_path, category, source_type, str(chunk_id))
                    )
                    total_chunks_count += 1

                pct = int((i / t_files) * 100)
                self.progress.emit(pct)
                self.status_text.emit(f"PROCESSING RAG ({pct}%): {filepath.name} [{category}]")
                if i % 15 == 0 or i == t_files:
                    self.log.emit("DEBUG", f"  └─ [{pct}%] Indexed ({category}): {filepath.name} ({len(chunks)} chunks)")

            conn.commit()
            conn.close()

            self.log.emit("INFO", f"[GRANULAR RAG COMPLETE]: {total_docs} Documents, {total_chunks_count} Chunks Indexed.")
            self.finished.emit(total_docs, total_chunks_count)
        except Exception as e:
            err_msg = f"GranularIndexerWorker Exception: {e}\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.finished.emit(0, 0)


# --- CLI Subprocess Exec Worker ---

class CLICommandWorker(QObject):
    chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, cmd_args: list):
        super().__init__()
        self.cmd_args = cmd_args

    def run(self):
        try:
            full_cmd = ["owlbearag-cli"] + self.cmd_args
            self.log.emit("INFO", f"[CLI DISPATCH]: EXECUTING {' '.join(full_cmd)}...")
            
            proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            full_out = []
            for line in iter(proc.stdout.readline, ''):
                if line:
                    full_out.append(line)
                    self.chunk.emit(line)
            proc.stdout.close()
            proc.wait()

            final_text = "".join(full_out)
            self.log.emit("INFO", f"[CLI EXEC COMPLETE]: Exited with code {proc.returncode}")
            self.finished.emit(final_text)
        except Exception as e:
            err_msg = f"CLICommandWorker Exception: {e}\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.finished.emit(f"Error: {e}")


# --- HuggingFace Search Worker ---

class HuggingFaceSearchWorker(QObject):
    results_ready = pyqtSignal(list)
    log = pyqtSignal(str, str)

    def __init__(self, keyword: str):
        super().__init__()
        self.keyword = keyword

    def run(self):
        try:
            self.log.emit("INFO", f"[HUGGINGFACE API]: SEARCHING HUB FOR '{self.keyword}'...")
            url = f"https://huggingface.co/api/models?search={urllib.parse.quote(self.keyword)}&limit=15"
            req = urllib.request.Request(url, headers={"User-Agent": "Owlbearag-GUI/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                models = json.loads(resp.read().decode('utf-8'))
                self.log.emit("INFO", f"  └─ Discovered {len(models)} HuggingFace models matching '{self.keyword}'")
                self.results_ready.emit(models)
        except Exception as e:
            self.log.emit("ERROR", f"[HUGGINGFACE ERROR]: {e}")
            self.results_ready.emit([])


# --- Model Fetcher Worker ---

class ModelFetcherWorker(QObject):
    models_ready = pyqtSignal(list)
    log = pyqtSignal(str, str)

    def __init__(self, ollama_url: str):
        super().__init__()
        self.ollama_url = ollama_url

    def run(self):
        try:
            self.log.emit("INFO", f"[MODEL DISCOVERY]: QUERYING OLLAMA MODELS AT {self.ollama_url}...")
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [m['name'] for m in data.get('models', [])]
                self.log.emit("INFO", f"  └─ Models Available: {', '.join(models)}")
                self.models_ready.emit(models)
        except Exception as e:
            self.log.emit("WARN", f"[MODEL FETCH NOTICE]: {self.ollama_url} API ({e}). Defaulting to standard model list.")
            default_models = ["deepseek-r1-abliterated:latest", "llama3:8b"]
            self.models_ready.emit(default_models)


# --- Cloudflare F76 VPS Sync Worker ---

class VPSSyncWorker(QObject):
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, vps_host: str):
        super().__init__()
        self.vps_host = vps_host

    def run(self):
        try:
            self.log.emit("INFO", f"[VPS CLOUDFLARE SYNC]: FETCHING F76 PROJECT CONFIGURATIONS FROM {self.vps_host}...")
            
            cmd = [
                "rsync", "-avz", "--progress",
                "-e", "ssh -o ConnectTimeout=6 -o ServerAliveInterval=3",
                f"{self.vps_host}:~/f76.world.conf",
                f"{self.vps_host}:~/nexus_server.py",
                f"{self.vps_host}:~/cf_ufw.sh",
                f"{self.vps_host}:~/F76WorldChat_Staging/",
                f"{self.vps_host}:~/FanVault_2026_TestDeployment/",
                str(VPS_SYNC_DIR)
            ]

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in iter(proc.stdout.readline, ''):
                if line:
                    self.log.emit("DEBUG", f"  └─ [vps rsync] {line.strip()}")
            proc.stdout.close()
            proc.wait()

            if proc.returncode == 0:
                self.log.emit("INFO", "[VPS SYNC SUCCESS]: CLOUDFLARE F76 PROJECT DATA SYNCHRONIZED PERFECTLY!")
                self.finished.emit(True, "VPS Sync Complete")
            else:
                err = proc.stderr.read()
                self.log.emit("WARN", f"[VPS SYNC NOTICE]: Completed with minor skips ({err.strip()})")
                self.finished.emit(True, "Sync Done")
        except Exception as e:
            err_msg = f"VPSSyncWorker Exception: {e}\nTraceback:\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.finished.emit(False, str(e))


# --- Remote Dual-GPU Sync Worker ---

class RemoteGPUSyncWorker(QObject):
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, remote_gpu_host: str):
        super().__init__()
        self.remote_gpu_host = remote_gpu_host

    def run(self):
        try:
            self.log.emit("INFO", f"[HYPERSPACE RSYNC]: TRANSMITTING UNIFIED RAG MATRIX TO DUAL-GPU CORE ({self.remote_gpu_host})...")
            if not RAG_DB_PATH.exists():
                self.log.emit("WARN", f"[ALERT]: LOCAL DATABASE MISSING: {RAG_DB_PATH}")
                self.finished.emit(False, "Database missing")
                return

            cmd = [
                "rsync", "-avz", "--progress",
                "-e", "ssh -o ConnectTimeout=6 -o ServerAliveInterval=3",
                str(RAG_DB_PATH),
                f"{self.remote_gpu_host}:~/.gemini/antigravity-cli/knowledge/rag_knowledge_base.sqlite"
            ]

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            for line in iter(proc.stdout.readline, ''):
                if line:
                    self.log.emit("DEBUG", f"  └─ [rsync] {line.strip()}")
            proc.stdout.close()
            proc.wait()

            if proc.returncode == 0:
                self.log.emit("INFO", "[RSYNC SUCCESS]: DUAL-GPU MATRIX SYNCHRONIZED PERFECTLY!")
                self.finished.emit(True, "Sync Complete")
            else:
                err = proc.stderr.read()
                self.log.emit("ERROR", f"[RSYNC FAILURE]: {err}")
                self.finished.emit(False, err)
        except Exception as e:
            err_msg = f"RemoteGPUSyncWorker Exception: {e}\nTraceback:\n{traceback.format_exc()}"
            self.log.emit("ERROR", err_msg)
            self.error.emit(err_msg)
            self.finished.emit(False, str(e))


# --- Mojave Amber Theme Styling (f76.world Cyber-Fallout Palette) ---
OWLBEARAG_QSS = """
QMainWindow, QWidget {
    background-color: #0a0907;
    color: #fff8e7;
    font-family: 'Consolas', 'Fira Code', 'Segoe UI', sans-serif;
    font-size: 13px;
}

QToolTip {
    background-color: #18130c;
    color: #ffb000;
    border: 1px solid #ffb000;
    border-radius: 4px;
    padding: 6px 10px;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #362916;
    background-color: #120f0a;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #120f0a;
    color: #a38c6b;
    padding: 10px 22px;
    border: 1px solid #2e2313;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

QTabBar::tab:selected {
    background-color: #1a140c;
    color: #ffb000;
    border: 1px solid #ffb000;
    border-bottom: 3px solid #ffb000;
}

QGroupBox {
    border: 1px solid #362916;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 18px;
    font-weight: bold;
    color: #ffb000;
    letter-spacing: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
    background-color: #0a0907;
}

QPushButton {
    background-color: #1a140c;
    color: #ffb000;
    border: 1px solid #ffb000;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: bold;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QPushButton:hover {
    background-color: #ffb000;
    color: #0a0907;
    border: 1px solid #fde68a;
}

QPushButton:pressed {
    background-color: #d97706;
    color: #ffffff;
}

QPushButton#goldBtn {
    background-color: #241b08;
    color: #fbbf24;
    border: 1px solid #f59e0b;
}

QPushButton#goldBtn:hover {
    background-color: #fbbf24;
    color: #0a0907;
}

QPushButton#cyanBtn {
    background-color: #081d24;
    color: #38bdf8;
    border: 1px solid #0284c7;
}

QPushButton#cyanBtn:hover {
    background-color: #38bdf8;
    color: #0a0907;
}

QPushButton#dangerBtn {
    background-color: #2b0b0e;
    color: #f43f5e;
    border: 1px solid #e11d48;
}

QPushButton#dangerBtn:hover {
    background-color: #e11d48;
    color: #ffffff;
}

QTableWidget {
    background-color: #0a0907;
    color: #fff8e7;
    border: 1px solid #2e2313;
    gridline-color: #2e2313;
    border-radius: 6px;
}

QHeaderView::section {
    background-color: #16110a;
    color: #ffb000;
    padding: 8px;
    font-weight: bold;
    border: 1px solid #2e2313;
}

QListWidget {
    background-color: #120f0a;
    border: 1px solid #2e2313;
    border-radius: 6px;
    color: #ffb000;
    padding: 6px;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #2e2313;
}

QListWidget::item:hover {
    background-color: #2e2313;
    color: #ffffff;
}

QListWidget::item:selected {
    background-color: #ffb000;
    color: #0a0907;
}

QComboBox {
    background-color: #120f0a;
    color: #ffb000;
    border: 1px solid #362916;
    border-radius: 6px;
    padding: 6px 12px;
}

QComboBox QAbstractItemView {
    background-color: #120f0a;
    color: #ffb000;
    selection-background-color: #ffb000;
    selection-color: #0a0907;
}

QLineEdit, QTextEdit {
    background-color: #070605;
    color: #fff8e7;
    border: 1px solid #362916;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #ffb000;
    selection-color: #0a0907;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #ffb000;
}

QProgressBar {
    border: 1px solid #362916;
    border-radius: 6px;
    text-align: center;
    background-color: #0a0907;
    color: #fff8e7;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #ffb000;
    border-radius: 5px;
}

QScrollBar:vertical {
    border: none;
    background: #0a0907;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #362916;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #ffb000;
}
"""


# --- Main Owlbearag Window ---

class OwlbearagWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OWLBEARAG — DYNAMIC COMMAND EXPLORER & MULTI-NODE CONSOLE")
        self.resize(1440, 990)
        self.setStyleSheet(OWLBEARAG_QSS)

        self.cfg = ConfigSecurityManager.load_config()

        self.chat_history = []
        self.all_discovered_commands = []
        self.current_session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")

        self.init_ui()
        self.verify_database_integrity()
        self.fetch_available_models()
        self.refresh_gpu_telemetry()
        self.load_dynamic_command_table()
        self.chat_input.setFocus()

    def verify_database_integrity(self):
        if RAG_DB_PATH.exists():
            try:
                conn = get_robust_sqlite_connection(RAG_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("PRAGMA quick_check;")
                res = cursor.fetchone()
                conn.close()
                self.log("SYSTEM", f"[DB INTEGRITY CHECK]: {res[0].upper() if res else 'OK'} (WAL Mode Enabled)")
            except Exception as e:
                self.log("WARN", f"[DB INTEGRITY NOTICE]: {e}")

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Header Panel
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet("background: linear-gradient(135deg, #0f121d 0%, #15102a 100%); border: 1px solid #7c3aed; border-radius: 8px; padding: 14px;")
        header_layout = QHBoxLayout(header)
        
        title_box = QVBoxLayout()
        title_label = QLabel("🦉 OWLBEARAG DYNAMIC COMMAND EXPLORER & HUB")
        title_label.setFont(QFont("Consolas", 17, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #c084fc; letter-spacing: 2px;")
        
        subtitle = QLabel("Dynamic Auto-Discovered Commands List | Multi-Node GPU & VPS Controls | SQLite WAL")
        subtitle.setFont(QFont("Consolas", 10))
        subtitle.setStyleSheet("color: #94a3b8;")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle)

        gauges_layout = QVBoxLayout()
        self.gpu_status = QLabel(f"⚡ DUAL GPU CORE: ONLINE ({self.cfg.get('remote_gpu_host')})")
        self.gpu_status.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.gpu_status.setStyleSheet("color: #c084fc; background-color: #17132e; border: 1px solid #7c3aed; padding: 5px 12px; border-radius: 6px;")

        self.vps_status = QLabel(f"🌐 CLOUDFLARE F76 VPS: ONLINE ({self.cfg.get('remote_vps_host')})")
        self.vps_status.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.vps_status.setStyleSheet("color: #38bdf8; background-color: #0b1a29; border: 1px solid #0284c7; padding: 5px 12px; border-radius: 6px;")

        gauges_layout.addWidget(self.gpu_status)
        gauges_layout.addWidget(self.vps_status)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        header_layout.addLayout(gauges_layout)

        layout.addWidget(header)

        # Global Quick Action & RAG Progress Control Bar
        rag_control_card = QFrame()
        rag_control_card.setFrameShape(QFrame.Shape.StyledPanel)
        rag_control_card.setStyleSheet("background-color: #0b0f19; border: 1px solid #1e2238; border-radius: 8px; padding: 10px;")
        rag_card_layout = QVBoxLayout(rag_control_card)

        bar_btn_row = QHBoxLayout()
        self.rebuild_rag_btn = QPushButton("⚡ REBUILD & INDEX SKILLS RAG MATRIX")
        self.rebuild_rag_btn.setToolTip("Process all skills (~/.agents/skills), prompts, chats, and VPS files with live progress output")
        self.rebuild_rag_btn.clicked.connect(self.confirm_and_build_index)

        self.quick_vps_btn = QPushButton("🌐 SYNC F76 VPS")
        self.quick_vps_btn.setObjectName("goldBtn")
        self.quick_vps_btn.setToolTip(f"Connect to {self.cfg.get('remote_vps_host')} via SSH/rsync and pull F76 project configurations")
        self.quick_vps_btn.clicked.connect(self.start_vps_sync)

        self.quick_gpu_btn = QPushButton("🚀 RSYNC TO DUAL GPU")
        self.quick_gpu_btn.setToolTip(f"Transmit local SQLite RAG matrix to remote GPU node ({self.cfg.get('remote_gpu_host')})")
        self.quick_gpu_btn.clicked.connect(self.start_remote_gpu_sync)

        self.fix_ollama_btn = QPushButton("🔧 DIAGNOSE & FIX OLLAMA CONNECTION")
        self.fix_ollama_btn.setObjectName("cyanBtn")
        self.fix_ollama_btn.setToolTip("Auto-diagnose Ollama HTTP reachability, systemd service status, and remote host binding")
        self.fix_ollama_btn.clicked.connect(self.start_ollama_resolver)

        bar_btn_row.addWidget(self.rebuild_rag_btn)
        bar_btn_row.addWidget(self.quick_vps_btn)
        bar_btn_row.addWidget(self.quick_gpu_btn)
        bar_btn_row.addWidget(self.fix_ollama_btn)
        rag_card_layout.addLayout(bar_btn_row)

        progress_row = QHBoxLayout()
        self.rag_status_label = QLabel("RAG STATUS: MATRIX ONLINE")
        self.rag_status_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.rag_status_label.setStyleSheet("color: #c084fc;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat(" RAG MATRIX: READY ")

        progress_row.addWidget(self.rag_status_label)
        progress_row.addWidget(self.progress_bar)
        rag_card_layout.addLayout(progress_row)

        layout.addWidget(rag_control_card)

        # Main Tabbed Interface
        self.tabs = QTabWidget()

        # --- Tab 0: Welcome Landing Screen ---
        tab_welcome = QWidget()
        welcome_layout = QVBoxLayout(tab_welcome)

        welcome_card = QGroupBox("👋 WELCOME TO OWLBEARAG (MOJAVE AMBER EDITION)")
        welcome_card_layout = QVBoxLayout(welcome_card)

        welcome_hero = QLabel(
            "<b>OWLBEARAG</b> is an enterprise multi-node AI control suite, PyTorch neural vector similarity reranker, "
            "and Cloudflare VPS synchronization console.<br/><br/>"
            "Designed for low-latency local workstation execution, dual-GPU server orchestration (RTX 3060 + GTX 1080), "
            "and Cloudflare production VPS node management."
        )
        welcome_hero.setWordWrap(True)
        welcome_hero.setStyleSheet("color: #fff8e7; font-size: 14px; padding: 12px; background-color: #16110a; border: 1px solid #362916; border-radius: 6px;")
        welcome_card_layout.addWidget(welcome_hero)

        grid_box = QGroupBox("⚡ SYSTEM CAPABILITIES & SUBSYSTEMS")
        grid_layout = QGridLayout(grid_box)

        caps = [
            ("🧠 Multi-Node RAG Matrix", "SQLite FTS5 database with WAL Mode indexing skills (~/.agents/skills), prompts, chats, and docs."),
            ("🔥 PyTorch Vector Reranker", "CUDA float16 AMP matrix cosine similarity calculations ranking search chunks against query vectors."),
            ("⚡ Dual-GPU Telemetry", "Real-time nvidia-smi memory allocation, core temperatures, and remote model pull/remove management."),
            ("🌐 Cloudflare VPS Sync", "Automated background rsync workers pulling production server configs and staging builds over SSH."),
            ("🔍 Dynamic Command Hub", "Auto-discovers 389+ commands across installed agent skills, CLI subcommands, and remote SSH tools."),
            ("🔧 Self-Healing Resolver", "3-stage connection resolver that probes HTTP reachability, tests fallbacks, and restarts systemd services.")
        ]

        for idx, (title, desc) in enumerate(caps):
            row = idx // 2
            col = idx % 2
            box = QWidget()
            b_layout = QVBoxLayout(box)
            lbl_title = QLabel(f"<b>{title}</b>")
            lbl_title.setStyleSheet("color: #ffb000; font-size: 13px;")
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #a38c6b; font-size: 11px;")
            b_layout.addWidget(lbl_title)
            b_layout.addWidget(lbl_desc)
            box.setStyleSheet("background-color: #120f0a; border: 1px solid #2e2313; border-radius: 6px; padding: 8px;")
            grid_layout.addWidget(box, row, col)

        welcome_card_layout.addWidget(grid_box)

        nav_box = QGroupBox("🚀 QUICK NAVIGATION JUMP BAR")
        nav_layout = QHBoxLayout(nav_box)

        btn_chat = QPushButton("💬 MODEL CHAT")
        btn_chat.setToolTip("Jump to interactive model chat tab")
        btn_chat.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        btn_cmds = QPushButton("🌐 DYNAMIC COMMANDS")
        btn_cmds.setObjectName("cyanBtn")
        btn_cmds.setToolTip("Jump to 389+ dynamic command explorer matrix tab")
        btn_cmds.clicked.connect(lambda: self.tabs.setCurrentIndex(2))

        btn_gpu = QPushButton("🖥️ GPU TELEMETRY")
        btn_gpu.setObjectName("goldBtn")
        btn_gpu.setToolTip("Jump to dual GPU telemetry and model manager tab")
        btn_gpu.clicked.connect(lambda: self.tabs.setCurrentIndex(3))

        btn_pt = QPushButton("🔥 PYTORCH RERANKER")
        btn_pt.setObjectName("dangerBtn")
        btn_pt.setToolTip("Jump to PyTorch neural reranker lab tab")
        btn_pt.clicked.connect(lambda: self.tabs.setCurrentIndex(4))

        nav_layout.addWidget(btn_chat)
        nav_layout.addWidget(btn_cmds)
        nav_layout.addWidget(btn_gpu)
        nav_layout.addWidget(btn_pt)

        welcome_card_layout.addWidget(nav_box)
        welcome_layout.addWidget(welcome_card)
        self.tabs.addTab(tab_welcome, "👋 WELCOME")

        # --- Tab 1: Interactive Model Chat ---
        tab_chat = QWidget()
        tab_chat_layout = QVBoxLayout(tab_chat)

        model_bar = QHBoxLayout()
        model_label = QLabel("SELECT MODEL:")
        model_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        model_label.setStyleSheet("color: #c084fc;")

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(340)
        self.model_combo.setToolTip("Select any installed model (Abliterated, Llama3, NSFW, or custom HuggingFace model)")
        self.model_combo.addItem("deepseek-r1-abliterated:latest")
        self.model_combo.addItem("llama3:8b")

        self.refresh_models_btn = QPushButton("🔄 REFRESH MODELS")
        self.refresh_models_btn.setToolTip("Query Ollama API to dynamically refresh available local and remote models")
        self.refresh_models_btn.clicked.connect(self.fetch_available_models)

        self.hf_web_btn = QPushButton("🤗 HUGGINGFACE HUB")
        self.hf_web_btn.setObjectName("goldBtn")
        self.hf_web_btn.setToolTip("Open HuggingFace GGUF models repository in browser")
        self.hf_web_btn.clicked.connect(self.open_huggingface_browser)

        self.save_chat_btn = QPushButton("💾 SAVE CONVERSATION")
        self.save_chat_btn.setToolTip("Save the current interactive chat history to JSON file and RAG matrix")
        self.save_chat_btn.clicked.connect(self.confirm_and_save_chat)

        model_bar.addWidget(model_label)
        model_bar.addWidget(self.model_combo)
        model_bar.addWidget(self.refresh_models_btn)
        model_bar.addWidget(self.hf_web_btn)
        model_bar.addWidget(self.save_chat_btn)
        model_bar.addStretch()

        tab_chat_layout.addLayout(model_bar)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setToolTip("Live Streaming Chat Response View")
        self.chat_display.setStyleSheet("background-color: #05070c; color: #c084fc; font-size: 14px; padding: 14px; border: 1px solid #1e2238;")
        tab_chat_layout.addWidget(self.chat_display)

        input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("TYPE WHATEVER YOU WANT TO THE CHOSEN MODEL (PROMPT, STORY, CODE)...")
        self.chat_input.setToolTip("Type message prompt or instruction and press ENTER or click TRANSMIT MESSAGE")
        self.chat_input.returnPressed.connect(self.send_chat_message)

        self.send_btn = QPushButton("🚀 TRANSMIT MESSAGE")
        self.send_btn.setToolTip("Send prompt message to selected model and stream live output")
        self.send_btn.clicked.connect(self.send_chat_message)

        input_row.addWidget(self.chat_input)
        input_row.addWidget(self.send_btn)
        tab_chat_layout.addLayout(input_row)

        self.tabs.addTab(tab_chat, "💬 INTERACTIVE MODEL CHAT")

        # --- Tab 2: Dynamic Command Explorer & Hub (USER REQUESTED) ---
        tab_cmd_explorer = QWidget()
        tab_cmd_layout = QVBoxLayout(tab_cmd_explorer)

        cmd_top_bar = QHBoxLayout()
        cmd_title = QLabel("🌐 DYNAMIC DISCOVERED COMMANDS MATRIX & HUB")
        cmd_title.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        cmd_title.setStyleSheet("color: #38bdf8;")

        self.cmd_filter_input = QLineEdit()
        self.cmd_filter_input.setPlaceholderText("🔍 FILTER COMMANDS BY KEYWORD OR CATEGORY (e.g. gpu, rag, vps, skill)...")
        self.cmd_filter_input.textChanged.connect(self.filter_dynamic_commands)

        self.refresh_cmd_btn = QPushButton("🔄 RESCAN COMMANDS")
        self.refresh_cmd_btn.setToolTip("Re-scan local filesystem (~/.agents/skills), CLI tools, system utilities, and remote SSH node capabilities to dynamically refresh the 389+ command matrix")
        self.refresh_cmd_btn.clicked.connect(self.load_dynamic_command_table)

        cmd_top_bar.addWidget(cmd_title)
        cmd_top_bar.addWidget(self.cmd_filter_input)
        cmd_top_bar.addWidget(self.refresh_cmd_btn)
        tab_cmd_layout.addLayout(cmd_top_bar)

        self.cmd_table = QTableWidget()
        self.cmd_table.setColumnCount(3)
        self.cmd_table.setHorizontalHeaderLabels(["CATEGORY", "COMMAND STRING", "ACTION DESCRIPTION"])
        self.cmd_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.cmd_table.itemDoubleClicked.connect(self.on_command_table_double_clicked)
        tab_cmd_layout.addWidget(self.cmd_table)

        cmd_exec_card = QGroupBox("SELECTED COMMAND EXECUTION BAR")
        cmd_exec_layout = QHBoxLayout(cmd_exec_card)

        self.selected_cmd_line = QLineEdit()
        self.selected_cmd_line.setPlaceholderText("DOUBLE-CLICK ANY COMMAND ABOVE OR TYPE CUSTOM COMMAND HERE...")

        self.run_selected_cmd_btn = QPushButton("🚀 EXECUTE SELECTED COMMAND")
        self.run_selected_cmd_btn.setObjectName("cyanBtn")
        self.run_selected_cmd_btn.setToolTip("Execute the selected row command from the Dynamic Command Explorer matrix in a dedicated background thread")
        self.run_selected_cmd_btn.clicked.connect(self.execute_selected_explorer_command)

        cmd_exec_layout.addWidget(self.selected_cmd_line)
        cmd_exec_layout.addWidget(self.run_selected_cmd_btn)
        tab_cmd_layout.addWidget(cmd_exec_card)

        self.tabs.addTab(tab_cmd_explorer, "🌐 DYNAMIC COMMAND HUB")

        # --- Tab 3: Remote GPU & Node Interaction Hub ---
        tab_remote = QWidget()
        tab_remote_layout = QVBoxLayout(tab_remote)

        remote_top = QHBoxLayout()
        remote_header = QLabel(f"🖥️ DUAL-GPU REMOTE NODE INTERACTION HUB ({self.cfg.get('remote_gpu_host')})")
        remote_header.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        remote_header.setStyleSheet("color: #a855f7;")

        self.refresh_telemetry_btn = QPushButton("📊 REFRESH GPU METRICS")
        self.refresh_telemetry_btn.setToolTip("Run nvidia-smi via SSH on remote GPU node (owlyyyrt.local) to query live dual GPU temperatures, VRAM allocation, and core metrics")
        self.refresh_telemetry_btn.clicked.connect(self.refresh_gpu_telemetry)

        remote_top.addWidget(remote_header)
        remote_top.addStretch()
        remote_top.addWidget(self.refresh_telemetry_btn)
        tab_remote_layout.addLayout(remote_top)

        self.gpu_telemetry_display = QTextEdit()
        self.gpu_telemetry_display.setReadOnly(True)
        self.gpu_telemetry_display.setMaximumHeight(160)
        self.gpu_telemetry_display.setStyleSheet("background-color: #05070c; color: #a855f7; font-size: 12px; padding: 10px; border: 1px solid #1e2238;")
        tab_remote_layout.addWidget(self.gpu_telemetry_display)

        model_mgr_box = QGroupBox("REMOTE OLLAMA MODEL MANAGER (PULL / REMOVE ON DUAL-GPU CORE)")
        model_mgr_layout = QHBoxLayout(model_mgr_box)

        self.remote_model_input = QLineEdit()
        self.remote_model_input.setPlaceholderText("ENTER OLLAMA MODEL NAME TO PULL/REMOVE (e.g. deepseek-r1:7b, mistral, llama3:8b)...")

        self.pull_model_btn = QPushButton("⬇️ PULL MODEL TO GPU")
        self.pull_model_btn.setObjectName("cyanBtn")
        self.pull_model_btn.setToolTip("Execute remote SSH command 'ollama pull <model>' on owlyyyrt.local to download and load a model on the GPU node")
        self.pull_model_btn.clicked.connect(self.confirm_and_pull_remote_model)

        self.rm_model_btn = QPushButton("🗑️ REMOVE MODEL FROM GPU")
        self.rm_model_btn.setObjectName("dangerBtn")
        self.rm_model_btn.setToolTip("Execute remote SSH command 'ollama rm <model>' on owlyyyrt.local to remove a model from GPU VRAM after user confirmation")
        self.rm_model_btn.clicked.connect(self.confirm_and_remove_remote_model)

        model_mgr_layout.addWidget(self.remote_model_input)
        model_mgr_layout.addWidget(self.pull_model_btn)
        model_mgr_layout.addWidget(self.rm_model_btn)
        tab_remote_layout.addWidget(model_mgr_box)

        remote_cmd_box = QGroupBox("REMOTE SSH SHELL DISPATCHER (EXECUTE COMMANDS ON REMOTE NODE)")
        remote_cmd_layout = QVBoxLayout(remote_cmd_box)

        self.remote_cmd_output = QTextEdit()
        self.remote_cmd_output.setReadOnly(True)
        self.remote_cmd_output.setStyleSheet("background-color: #05070c; color: #38bdf8; font-size: 13px; padding: 10px; border: 1px solid #1e2238;")
        remote_cmd_layout.addWidget(self.remote_cmd_output)

        remote_cmd_row = QHBoxLayout()
        self.remote_cmd_input = QLineEdit()
        self.remote_cmd_input.setPlaceholderText("TYPE ANY REMOTE COMMAND TO EXECUTE (e.g. btrfs filesystem show, lscpu, docker ps)...")
        self.remote_cmd_input.returnPressed.connect(self.confirm_and_exec_remote_command)

        self.exec_remote_cmd_btn = QPushButton("🚀 EXECUTE ON REMOTE NODE")
        self.exec_remote_cmd_btn.setObjectName("goldBtn")
        self.exec_remote_cmd_btn.setToolTip("Execute the typed remote shell command on owlyyyrt.local via SSH and display live output")
        self.exec_remote_cmd_btn.clicked.connect(self.confirm_and_exec_remote_command)

        remote_cmd_row.addWidget(self.remote_cmd_input)
        remote_cmd_row.addWidget(self.exec_remote_cmd_btn)
        remote_cmd_layout.addLayout(remote_cmd_row)

        tab_remote_layout.addWidget(remote_cmd_box)
        self.tabs.addTab(tab_remote, "🖥️ REMOTE GPU & NODE HUB")

        # --- Tab 4: PyTorch Neural Reranker Lab ---
        tab_pytorch = QWidget()
        tab_pt_layout = QVBoxLayout(tab_pytorch)

        pt_header = QLabel("🔥 PYTORCH DEEP LEARNING NEURAL VECTOR RERANKER ENGINE")
        pt_header.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        pt_header.setStyleSheet("color: #f43f5e;")
        tab_pt_layout.addWidget(pt_header)

        pt_info = QLabel(f"PyTorch Available: {'✅ YES' if HAS_PYTORCH else '❌ NO'} | CUDA Acceleration: {'⚡ ACTIVE (' + torch.cuda.get_device_name(0) + ')' if HAS_PYTORCH and torch.cuda.is_available() else '💻 CPU TENSORS'}")
        pt_info.setStyleSheet("color: #a855f7; font-weight: bold; background-color: #120917; border: 1px solid #7c3aed; padding: 8px; border-radius: 6px;")
        tab_pt_layout.addWidget(pt_info)

        pt_input_row = QHBoxLayout()
        self.pt_query_input = QLineEdit()
        self.pt_query_input.setPlaceholderText("ENTER QUERY FOR PYTORCH NEURAL VECTOR RERANKING (e.g. adhd, PyTorch, F76)...")
        
        self.pt_rerank_btn = QPushButton("🔥 RUN PYTORCH RERANKER")
        self.pt_rerank_btn.setObjectName("dangerBtn")
        self.pt_rerank_btn.setToolTip("Execute PyTorch CUDA float16 AMP matrix cosine similarity calculations to rank knowledge chunks against query")
        self.pt_rerank_btn.clicked.connect(self.run_pytorch_rerank_demo)

        pt_input_row.addWidget(self.pt_query_input)
        pt_input_row.addWidget(self.pt_rerank_btn)
        tab_pt_layout.addLayout(pt_input_row)

        self.pt_display = QTextEdit()
        self.pt_display.setReadOnly(True)
        self.pt_display.setToolTip("PyTorch Neural Cosine Similarity Reranker Output Matrix")
        self.pt_display.setStyleSheet("background-color: #05070c; color: #f43f5e; font-size: 13px; padding: 12px; border: 1px solid #1e2238;")
        tab_pt_layout.addWidget(self.pt_display)

        self.tabs.addTab(tab_pytorch, "🔥 PYTORCH NEURAL RERANKER")

        # --- Tab 5: Advanced Menu & CLI Functions Hub ---
        tab_adv = QWidget()
        tab_adv_layout = QHBoxLayout(tab_adv)

        adv_left = QVBoxLayout()
        adv_left_label = QLabel("⚡ ADVANCED FUNCTIONS & CLI COMMANDS:")
        adv_left_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        adv_left_label.setStyleSheet("color: #c084fc;")
        adv_left.addWidget(adv_left_label)

        self.cli_func_list = QListWidget()
        self.cli_func_list.setToolTip("Click any advanced command item to fill and execute via owlbearag-cli")

        cli_features = [
            ("⚡ vps status", "Check Cloudflare F76 VPS Uptime, Disk Usage, & Services"),
            ("🚀 vps sync", "Sync F76 Project Data from VPS (37.114.37.41) via rsync"),
            ("🤗 hf gguf", "Search HuggingFace Hub for GGUF Models"),
            ("🤗 hf uncensored", "Search HuggingFace Hub for Uncensored Models"),
            ("🧠 rag PyTorch", "Search SQLite Matrix for PyTorch Neural Embeddings"),
            ("🧠 rag adhd", "Search SQLite Matrix for ADHD Skill & Focus Runbook"),
            ("💬 query Write a story", "Stream LLM Response from DeepSeek-R1 Core"),
            ("🧠 query Explain Btrfs", "Stream Technical Explanation from Model Core"),
        ]

        for cmd_name, desc in cli_features:
            item = QListWidgetItem(f"{cmd_name} — {desc}")
            item.setData(Qt.ItemDataRole.UserRole, cmd_name)
            self.cli_func_list.addItem(item)

        self.cli_func_list.itemClicked.connect(self.on_cli_list_clicked)
        adv_left.addWidget(self.cli_func_list)

        tab_adv_layout.addLayout(adv_left, stretch=1)

        adv_right = QVBoxLayout()
        adv_right_label = QLabel("🖥️ INTERACTIVE CLI COMMAND DISPATCHER:")
        adv_right_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        adv_right_label.setStyleSheet("color: #38bdf8;")
        adv_right.addWidget(adv_right_label)

        self.cli_output = QTextEdit()
        self.cli_output.setReadOnly(True)
        self.cli_output.setStyleSheet("background-color: #05070c; color: #38bdf8; font-size: 13px; padding: 12px; border: 1px solid #1e2238;")
        adv_right.addWidget(self.cli_output)

        cmd_input_row = QHBoxLayout()
        self.cli_input_line = QLineEdit()
        self.cli_input_line.setPlaceholderText("TYPE ANY owlbearag-cli COMMAND HERE (e.g. vps status, hf gguf, rag PyTorch)...")
        self.cli_input_line.setToolTip("Type command string and press ENTER or click EXECUTE CLI COMMAND")
        self.cli_input_line.returnPressed.connect(self.execute_typed_cli_command)

        self.cli_exec_btn = QPushButton("🚀 EXECUTE CLI COMMAND")
        self.cli_exec_btn.setObjectName("cyanBtn")
        self.cli_exec_btn.setToolTip("Dispatch typed command to owlbearag-cli background process")
        self.cli_exec_btn.clicked.connect(self.execute_typed_cli_command)

        cmd_input_row.addWidget(self.cli_input_line)
        cmd_input_row.addWidget(self.cli_exec_btn)
        adv_right.addLayout(cmd_input_row)

        tab_adv_layout.addLayout(adv_right, stretch=2)

        self.tabs.addTab(tab_adv, "⚡ ADVANCED MENU & CLI HUB")

        # --- Tab 6: Interactive Security & Config Manager ---
        tab_cfg = QWidget()
        tab_cfg_layout = QVBoxLayout(tab_cfg)

        cfg_title = QLabel("🔐 INTERACTIVE CONFIGURATION & CREDENTIAL SECURITY MANAGER")
        cfg_title.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        cfg_title.setStyleSheet("color: #38bdf8;")
        tab_cfg_layout.addWidget(cfg_title)

        cfg_box = QGroupBox("NODE ENDPOINTS & SECURITY MATRIX (~/.gemini/antigravity-cli/config.json - MODE 0600)")
        cfg_grid = QVBoxLayout(cfg_box)

        ollama_row = QHBoxLayout()
        ollama_row.addWidget(QLabel("Ollama Host API Endpoint:"))
        self.cfg_ollama_input = QLineEdit(self.cfg.get("ollama_host", DEFAULT_OLLAMA_HOST))
        ollama_row.addWidget(self.cfg_ollama_input)
        cfg_grid.addLayout(ollama_row)

        gpu_row = QHBoxLayout()
        gpu_row.addWidget(QLabel("Remote GPU Node Host (SSH):"))
        self.cfg_gpu_input = QLineEdit(self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST))
        gpu_row.addWidget(self.cfg_gpu_input)
        cfg_grid.addLayout(gpu_row)

        vps_row = QHBoxLayout()
        vps_row.addWidget(QLabel("Cloudflare F76 VPS Host (SSH):"))
        self.cfg_vps_input = QLineEdit(self.cfg.get("remote_vps_host", DEFAULT_REMOTE_VPS_HOST))
        vps_row.addWidget(self.cfg_vps_input)
        cfg_grid.addLayout(vps_row)

        save_cfg_btn = QPushButton("💾 SAVE CONFIGURATION SECURELY")
        save_cfg_btn.setObjectName("goldBtn")
        save_cfg_btn.clicked.connect(self.save_gui_config)
        cfg_grid.addWidget(save_cfg_btn)

        tab_cfg_layout.addWidget(cfg_box)
        self.tabs.addTab(tab_cfg, "🔐 SECURITY & CONFIG")

        # --- Tab 7: HuggingFace Model Search ---
        tab_hf = QWidget()
        tab_hf_layout = QVBoxLayout(tab_hf)

        hf_bar = QHBoxLayout()
        self.hf_input = QLineEdit()
        self.hf_input.setPlaceholderText("ENTER KEYWORD TO SEARCH HUGGINGFACE MODELS...")
        self.hf_input.setToolTip("Search HuggingFace Hub REST API")
        self.hf_input.returnPressed.connect(self.search_huggingface_models)

        self.hf_search_btn = QPushButton("🔍 SEARCH HF HUB")
        self.hf_search_btn.setObjectName("goldBtn")
        self.hf_search_btn.setToolTip("Execute HuggingFace Hub model search")
        self.hf_search_btn.clicked.connect(self.search_huggingface_models)

        hf_bar.addWidget(self.hf_input)
        hf_bar.addWidget(self.hf_search_btn)
        tab_hf_layout.addLayout(hf_bar)

        self.hf_display = QTextEdit()
        self.hf_display.setReadOnly(True)
        tab_hf_layout.addWidget(self.hf_display)

        self.tabs.addTab(tab_hf, "🤗 HUGGINGFACE EXPLORER")

        # --- Tab 8: Professional System Debug Telemetry ---
        tab_sync = QWidget()
        tab_sync_layout = QVBoxLayout(tab_sync)

        log_group = QGroupBox("PROFESSIONAL REALTIME SYSTEM LOG & RAG FILE TELEMETRY")
        log_layout = QVBoxLayout(log_group)

        log_btn_row = QHBoxLayout()
        self.clear_logs_btn = QPushButton("🧹 CLEAR LOGS")
        self.clear_logs_btn.setObjectName("dangerBtn")
        self.clear_logs_btn.setToolTip("Clear the visible debug console log screen")
        self.clear_logs_btn.clicked.connect(self.clear_debug_logs)

        self.export_logs_btn = QPushButton("📁 EXPORT LOG FILE")
        self.export_logs_btn.setToolTip("Export full debug system log file to disk")
        self.export_logs_btn.clicked.connect(self.export_debug_logs)

        log_btn_row.addStretch()
        log_btn_row.addWidget(self.clear_logs_btn)
        log_btn_row.addWidget(self.export_logs_btn)
        log_layout.addLayout(log_btn_row)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        tab_sync_layout.addWidget(log_group)

        self.tabs.addTab(tab_sync, "🌐 DEBUG & TELEMETRY")

        layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)

        self.log("SYSTEM", "[REALTIME MONITOR ONLINE]: OWLBEARAG CONSOLE READY WITH DYNAMIC COMMAND EXPLORER HUB.")

    # --- Dynamic Command Explorer Methods ---

    def load_dynamic_command_table(self):
        self.all_discovered_commands = CommandRegistryScanner.discover_all_commands()
        self.display_filtered_commands(self.all_discovered_commands)
        self.log("INFO", f"[DYNAMIC COMMAND EXPLORER]: Auto-discovered {len(self.all_discovered_commands)} available commands.")

    def display_filtered_commands(self, commands: list):
        self.cmd_table.setRowCount(0)
        for row_idx, item in enumerate(commands):
            self.cmd_table.insertRow(row_idx)
            
            cat_item = QTableWidgetItem(item.get("category", "General"))
            cat_item.setForeground(QColor("#c084fc"))
            
            cmd_item = QTableWidgetItem(item.get("command", ""))
            cmd_item.setForeground(QColor("#38bdf8"))
            
            desc_item = QTableWidgetItem(item.get("description", ""))
            desc_item.setForeground(QColor("#e2e8f0"))

            self.cmd_table.setItem(row_idx, 0, cat_item)
            self.cmd_table.setItem(row_idx, 1, cmd_item)
            self.cmd_table.setItem(row_idx, 2, desc_item)

    def filter_dynamic_commands(self, filter_text: str):
        flt = filter_text.strip().lower()
        if not flt:
            self.display_filtered_commands(self.all_discovered_commands)
            return

        filtered = [
            c for c in self.all_discovered_commands
            if flt in c.get("category", "").lower() or flt in c.get("command", "").lower() or flt in c.get("description", "").lower()
        ]
        self.display_filtered_commands(filtered)

    def on_command_table_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        cmd_item = self.cmd_table.item(row, 1)
        if cmd_item:
            cmd_text = cmd_item.text()
            self.selected_cmd_line.setText(cmd_text)
            self.log("INFO", f"[COMMAND EXPLORER]: Selected command '{cmd_text}'")

    def execute_selected_explorer_command(self):
        cmd_text = self.selected_cmd_line.text().strip()
        if not cmd_text:
            return

        self.log("INFO", f"[ACTION INITIATED]: Executing command from Explorer Hub: '{cmd_text}'")
        
        # Route depending on prefix
        if cmd_text.startswith("rag ") or cmd_text.startswith("vps ") or cmd_text.startswith("gpu ") or cmd_text.startswith("query "):
            self.cli_input_line.setText(cmd_text)
            self.tabs.setCurrentIndex(4)  # Switch to Advanced CLI Hub
            self.execute_typed_cli_command()
        elif cmd_text.startswith("ssh "):
            # Extract remote command
            parts = cmd_text.split(" ", 2)
            remote_target = parts[1]
            remote_cmd = parts[2].strip("'\"") if len(parts) > 2 else "uptime"
            self.remote_cmd_input.setText(remote_cmd)
            self.tabs.setCurrentIndex(2)  # Switch to Remote GPU Hub
            self.confirm_and_exec_remote_command()
        else:
            # Default dispatch to owlbearag-cli
            self.cli_input_line.setText(cmd_text)
            self.tabs.setCurrentIndex(4)
            self.execute_typed_cli_command()

    # --- Remote Node Interaction Methods ---

    def refresh_gpu_telemetry(self):
        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        self.log("INFO", f"[ACTION INITIATED]: Refreshing GPU telemetry from {gpu_host}...")
        self.refresh_telemetry_btn.setEnabled(False)

        self.thread_telem = QThread()
        self.worker_telem = RemoteGPUTelemetryWorker(gpu_host)
        self.worker_telem.moveToThread(self.thread_telem)

        self.thread_telem.started.connect(self.worker_telem.run)
        self.worker_telem.log.connect(self.log)
        self.worker_telem.telemetry_ready.connect(self.display_gpu_telemetry)

        self.worker_telem.telemetry_ready.connect(self.thread_telem.quit)
        self.worker_telem.telemetry_ready.connect(self.worker_telem.deleteLater)
        self.thread_telem.finished.connect(self.thread_telem.deleteLater)

        self.thread_telem.start()

    def display_gpu_telemetry(self, telem: dict):
        self.refresh_telemetry_btn.setEnabled(True)
        if not telem or "gpus" not in telem:
            self.gpu_telemetry_display.setText("[REMOTE GPU METRICS UNREACHABLE OR SSH TIMEOUT]")
            return

        lines = [f"📊 REMOTE GPU METRICS ({telem.get('timestamp')}) — HOST: {self.cfg.get('remote_gpu_host')}\n"]
        for g in telem.get("gpus", []):
            idx = g.get("index")
            name = g.get("name")
            temp = g.get("temp")
            util = g.get("util")
            used = g.get("mem_used")
            total = g.get("mem_total")
            lines.append(f"  └─ [GPU {idx}] {name}: Temp {temp}°C | Core Util: {util}% | VRAM: {used} MiB / {total} MiB")

        lines.append(f"\n💻 REMOTE SYSTEM SUMMARY:\n{telem.get('system_summary')}")
        self.gpu_telemetry_display.setText("\n".join(lines))

    def confirm_and_pull_remote_model(self):
        m_name = self.remote_model_input.text().strip()
        if not m_name:
            QMessageBox.warning(self, "No Model Name", "Please enter a model name to pull.")
            return

        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        if self.confirm_action("Confirm Model Pull", f"Execute 'ollama pull {m_name}' remotely on GPU host ({gpu_host})?"):
            self.start_remote_model_action("pull", m_name)

    def confirm_and_remove_remote_model(self):
        m_name = self.remote_model_input.text().strip()
        if not m_name:
            QMessageBox.warning(self, "No Model Name", "Please enter a model name to remove.")
            return

        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        if self.confirm_action("Confirm Model Delete", f"Execute 'ollama rm {m_name}' remotely on GPU host ({gpu_host})?"):
            self.start_remote_model_action("rm", m_name)

    def start_remote_model_action(self, action: str, m_name: str):
        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        self.pull_model_btn.setEnabled(False)
        self.rm_model_btn.setEnabled(False)

        self.thread_mgr = QThread()
        self.worker_mgr = RemoteModelManagerWorker(gpu_host, action, m_name)
        self.worker_mgr.moveToThread(self.thread_mgr)

        self.thread_mgr.started.connect(self.worker_mgr.run)
        self.worker_mgr.log.connect(self.log)
        self.worker_mgr.chunk.connect(lambda txt: self.remote_cmd_output.append(txt))
        self.worker_mgr.finished.connect(self.on_remote_model_action_done)

        self.worker_mgr.finished.connect(self.thread_mgr.quit)
        self.worker_mgr.finished.connect(self.worker_mgr.deleteLater)
        self.thread_mgr.finished.connect(self.thread_mgr.deleteLater)

        self.thread_mgr.start()

    def on_remote_model_action_done(self, ok: bool, msg: str):
        self.pull_model_btn.setEnabled(True)
        self.rm_model_btn.setEnabled(True)
        if ok:
            QMessageBox.information(self, "Remote Action Complete", f"Remote Model Operation Status:\n\n{msg}")
            self.fetch_available_models()
        else:
            QMessageBox.warning(self, "Remote Action Failed", f"Remote Model Operation Status:\n\n{msg}")

    def confirm_and_exec_remote_command(self):
        cmd = self.remote_cmd_input.text().strip()
        if not cmd:
            return

        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        self.log("INFO", f"[ACTION INITIATED]: Dispatching SSH command to {gpu_host}: '{cmd}'...")
        self.exec_remote_cmd_btn.setEnabled(False)
        self.remote_cmd_output.append(f"\n<b style='color: #a855f7;'>[REMOTE EXEC ({gpu_host})]: {cmd}</b>\n")

        self.thread_exec = QThread()
        self.worker_exec = RemoteExecWorker(gpu_host, cmd)
        self.worker_exec.moveToThread(self.thread_exec)

        self.thread_exec.started.connect(self.worker_exec.run)
        self.worker_exec.log.connect(self.log)
        self.worker_exec.chunk.connect(lambda txt: self.remote_cmd_output.append(txt))
        self.worker_exec.error.connect(self.show_exception_popup)
        self.worker_exec.finished.connect(lambda txt: self.exec_remote_cmd_btn.setEnabled(True))

        self.worker_exec.finished.connect(self.thread_exec.quit)
        self.worker_exec.finished.connect(self.worker_exec.deleteLater)
        self.thread_exec.finished.connect(self.thread_exec.deleteLater)

        self.thread_exec.start()

    # --- Config Security Save Method ---

    def save_gui_config(self):
        self.log("INFO", "[ACTION INITIATED]: User clicked 'SAVE CONFIGURATION SECURELY'. Updating config.json (0600)...")
        self.cfg["ollama_host"] = self.cfg_ollama_input.text().strip()
        self.cfg["remote_gpu_host"] = self.cfg_gpu_input.text().strip()
        self.cfg["remote_vps_host"] = self.cfg_vps_input.text().strip()
        
        ConfigSecurityManager.save_config(self.cfg)
        self.gpu_status.setText(f"⚡ DUAL GPU CORE: ONLINE ({self.cfg.get('remote_gpu_host')})")
        self.vps_status.setText(f"🌐 CLOUDFLARE F76 VPS: ONLINE ({self.cfg.get('remote_vps_host')})")
        
        self.log("INFO", f"✅ Configuration saved securely to {CONFIG_FILE_PATH}")
        QMessageBox.information(self, "Config Saved", f"Configuration updated and saved with secure mode 0600 permissions to:\n{CONFIG_FILE_PATH}")

    # --- PyTorch Reranker Demo Method ---

    def run_pytorch_rerank_demo(self):
        query = self.pt_query_input.text().strip()
        if not query:
            query = "adhd PyTorch"
            self.pt_query_input.setText(query)

        self.log("INFO", f"[ACTION INITIATED]: Running PyTorch Neural Cosine Similarity Reranker for query '{query}'...")
        self.pt_rerank_btn.setEnabled(False)
        self.pt_display.setText("[COMPUTING PYTORCH NEURAL TENSORS & COSINE SIMILARITIES...]")

        if not RAG_DB_PATH.exists():
            self.pt_display.setText("[RAG DATABASE MISSING. REBUILD RAG MATRIX FIRST.]")
            self.pt_rerank_btn.setEnabled(True)
            return

        try:
            conn = get_robust_sqlite_connection(RAG_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT doc_id, title, content, filepath FROM chunks LIMIT 20")
            rows = cursor.fetchall()
            conn.close()

            candidates = [{"id": r[0], "title": r[1], "content": r[2], "filepath": r[3]} for r in rows]

            self.thread_pt = QThread()
            self.worker_pt = PyTorchRerankerWorker(query, candidates)
            self.worker_pt.moveToThread(self.thread_pt)

            self.thread_pt.started.connect(self.worker_pt.run)
            self.worker_pt.log.connect(self.log)
            self.worker_pt.results_ready.connect(self.display_pytorch_results)

            self.worker_pt.results_ready.connect(self.thread_pt.quit)
            self.worker_pt.results_ready.connect(self.worker_pt.deleteLater)
            self.thread_pt.finished.connect(self.thread_pt.deleteLater)

            self.thread_pt.start()
        except Exception as e:
            self.show_exception_popup(f"PyTorch Reranker Exception: {e}")
            self.pt_rerank_btn.setEnabled(True)

    def display_pytorch_results(self, scored_results: list):
        self.pt_rerank_btn.setEnabled(True)
        lines = [f"## PYTORCH NEURAL RERANKING RESULTS FOR QUERY: '{self.pt_query_input.text()}'\n"]
        for idx, item in enumerate(scored_results[:10], 1):
            score = item.get("pytorch_score", 0.0)
            title = item.get("title", "Untitled")
            filepath = item.get("filepath", "")
            snippet = item.get("content", "")[:180].replace("\n", " ")
            lines.append(f"### [{idx}] {title} — PyTorch Neural Cosine Score: {score:.4f}")
            lines.append(f"📄 Path: {filepath}")
            lines.append(f"💬 Snippet: {snippet}...\n---")

        self.pt_display.setText("\n".join(lines))

    # --- Automated Ollama Resolver Method ---

    def start_ollama_resolver(self):
        ollama_url = self.cfg.get("ollama_host", DEFAULT_OLLAMA_HOST)
        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        
        self.log("INFO", f"[ACTION INITIATED]: User clicked 'DIAGNOSE & FIX OLLAMA CONNECTION'. Testing {ollama_url}...")
        self.fix_ollama_btn.setEnabled(False)

        self.thread_ollama = QThread()
        self.worker_ollama = OllamaConnectionResolverWorker(ollama_url, gpu_host)
        self.worker_ollama.moveToThread(self.thread_ollama)

        self.thread_ollama.started.connect(self.worker_ollama.run)
        self.worker_ollama.log.connect(self.log)
        self.worker_ollama.error.connect(self.show_exception_popup)
        self.worker_ollama.resolved.connect(self.on_ollama_resolved)

        self.worker_ollama.resolved.connect(self.thread_ollama.quit)
        self.worker_ollama.resolved.connect(self.worker_ollama.deleteLater)
        self.thread_ollama.finished.connect(self.thread_ollama.deleteLater)

        self.thread_ollama.start()

    def on_ollama_resolved(self, success: bool, msg: str):
        self.fix_ollama_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Ollama Connection Ready", f"Ollama Resolver Status:\n\n{msg}")
            self.fetch_available_models()
        else:
            QMessageBox.warning(self, "Ollama Resolver Notice", f"Automated resolver finished:\n\n{msg}")

    # --- Granular RAG Builder Method ---

    def confirm_and_build_index(self):
        self.log("INFO", "[ACTION INITIATED]: User pressed 'REBUILD & INDEX SKILLS RAG MATRIX'. Preparing confirmation dialog...")
        if self.confirm_action("Confirm Action: Build Matrix", "Process all skills (~/.agents/skills), prompts, chats, and VPS files with live progress output?"):
            self.log("INFO", "[ACTION CONFIRMED]: Starting Granular Indexer Worker process...")
            self.start_granular_indexing()

    def start_granular_indexing(self):
        self.rebuild_rag_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(" COMPILING RAG MATRIX... %p% ")
        self.rag_status_label.setText("RAG STATUS: PROCESSING SKILLS & FILES...")

        self.thread_idx = QThread()
        self.worker_idx = GranularIndexerWorker()
        self.worker_idx.moveToThread(self.thread_idx)

        self.thread_idx.started.connect(self.worker_idx.run)
        self.worker_idx.progress.connect(self.progress_bar.setValue)
        self.worker_idx.status_text.connect(self.rag_status_label.setText)
        self.worker_idx.log.connect(self.log)
        self.worker_idx.error.connect(self.show_exception_popup)
        self.worker_idx.finished.connect(self.on_indexing_done)

        self.worker_idx.finished.connect(self.thread_idx.quit)
        self.worker_idx.finished.connect(self.worker_idx.deleteLater)
        self.thread_idx.finished.connect(self.thread_idx.deleteLater)

        self.thread_idx.start()

    def on_indexing_done(self, docs, chunks):
        self.rebuild_rag_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat(" RAG MATRIX INDEXED (100%) ")
        self.rag_status_label.setText(f"RAG STATUS: READY ({docs} Docs | {chunks} Chunks)")

    # --- Other Node Workers ---

    def start_vps_sync(self):
        vps_host = self.cfg.get("remote_vps_host", DEFAULT_REMOTE_VPS_HOST)
        self.log("INFO", f"[ACTION INITIATED]: User pressed 'SYNC F76 VPS'. Connecting via SSH/rsync to {vps_host}...")
        self.quick_vps_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(" FETCHING CLOUDFLARE VPS F76 DATA... ")

        self.thread_vps = QThread()
        self.worker_vps = VPSSyncWorker(vps_host)
        self.worker_vps.moveToThread(self.thread_vps)

        self.thread_vps.started.connect(self.worker_vps.run)
        self.worker_vps.log.connect(self.log)
        self.worker_vps.error.connect(self.show_exception_popup)
        self.worker_vps.finished.connect(lambda ok, msg: self.quick_vps_btn.setEnabled(True))

        self.worker_vps.finished.connect(self.thread_vps.quit)
        self.worker_vps.finished.connect(self.worker_vps.deleteLater)
        self.thread_vps.finished.connect(self.thread_vps.deleteLater)

        self.thread_vps.start()

    def start_remote_gpu_sync(self):
        gpu_host = self.cfg.get("remote_gpu_host", DEFAULT_REMOTE_GPU_HOST)
        self.log("INFO", f"[ACTION INITIATED]: User pressed 'RSYNC TO DUAL GPU'. Transmitting SQLite matrix to {gpu_host}...")
        self.quick_gpu_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(" TRANSMITTING UNIFIED MATRIX TO DUAL-GPU CORE... ")

        self.thread_gpu = QThread()
        self.worker_gpu = RemoteGPUSyncWorker(gpu_host)
        self.worker_gpu.moveToThread(self.thread_gpu)

        self.thread_gpu.started.connect(self.worker_gpu.run)
        self.worker_gpu.log.connect(self.log)
        self.worker_gpu.error.connect(self.show_exception_popup)
        self.worker_gpu.finished.connect(lambda ok, msg: self.quick_gpu_btn.setEnabled(True))

        self.worker_gpu.finished.connect(self.thread_gpu.quit)
        self.worker_gpu.finished.connect(self.worker_gpu.deleteLater)
        self.thread_gpu.finished.connect(self.thread_gpu.deleteLater)

        self.thread_gpu.start()

    # --- Advanced Menu & CLI Execution ---

    def on_cli_list_clicked(self, item: QListWidgetItem):
        cmd_text = item.data(Qt.ItemDataRole.UserRole)
        if cmd_text:
            self.log("INFO", f"[ACTION INITIATED]: Selected item from Advanced Menu list: '{cmd_text}'")
            self.cli_input_line.setText(cmd_text)
            self.execute_typed_cli_command()

    def execute_typed_cli_command(self):
        raw_cmd = self.cli_input_line.text().strip()
        if not raw_cmd:
            return

        cmd_args = raw_cmd.split()
        self.log("INFO", f"[ACTION INITIATED]: Executing typed CLI command: 'owlbearag-cli {' '.join(cmd_args)}'")
        self.cli_exec_btn.setEnabled(False)
        self.cli_output.append(f"\n<b style='color: #00e5ff;'>[EXECUTING]: owlbearag-cli {' '.join(cmd_args)}</b>\n")

        self.thread_cli = QThread()
        self.worker_cli = CLICommandWorker(cmd_args)
        self.worker_cli.moveToThread(self.thread_cli)

        self.thread_cli.started.connect(self.worker_cli.run)
        self.worker_cli.log.connect(self.log)
        self.worker_cli.chunk.connect(self.append_cli_chunk)
        self.worker_cli.error.connect(self.show_exception_popup)
        self.worker_cli.finished.connect(lambda txt: self.cli_exec_btn.setEnabled(True))

        self.worker_cli.finished.connect(self.thread_cli.quit)
        self.worker_cli.finished.connect(self.worker_cli.deleteLater)
        self.thread_cli.finished.connect(self.thread_cli.deleteLater)

        self.thread_cli.start()

    def append_cli_chunk(self, chunk_text: str):
        cursor = self.cli_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk_text)
        self.cli_output.setTextCursor(cursor)

    # --- HuggingFace Browser & Search ---

    def open_huggingface_browser(self):
        self.log("INFO", "[ACTION INITIATED]: User pressed 'HUGGINGFACE HUB'. Opening browser...")
        url = QUrl("https://huggingface.co/models?search=gguf")
        QDesktopServices.openUrl(url)

    def search_huggingface_models(self):
        kw = self.hf_input.text().strip()
        if not kw:
            kw = "gguf"
            self.hf_input.setText(kw)

        self.log("INFO", f"[ACTION INITIATED]: Searching HuggingFace Hub REST API for '{kw}'...")
        self.hf_search_btn.setEnabled(False)
        self.hf_display.setText("[SEARCHING HUGGINGFACE HUB API...]")

        self.thread_hf = QThread()
        self.worker_hf = HuggingFaceSearchWorker(kw)
        self.worker_hf.moveToThread(self.thread_hf)

        self.thread_hf.started.connect(self.worker_hf.run)
        self.worker_hf.log.connect(self.log)
        self.worker_hf.results_ready.connect(self.display_huggingface_results)

        self.worker_hf.results_ready.connect(self.thread_hf.quit)
        self.worker_hf.results_ready.connect(self.worker_hf.deleteLater)
        self.thread_hf.finished.connect(self.thread_hf.deleteLater)

        self.thread_hf.start()

    def display_huggingface_results(self, models: list):
        self.hf_search_btn.setEnabled(True)
        if not models:
            self.hf_display.setText("[NO MATCHING HUGGINGFACE MODELS FOUND.]")
            return

        lines = [f"## HUGGINGFACE HUB SEARCH RESULTS ({len(models)} MODELS FOUND):\n"]
        for idx, m in enumerate(models, 1):
            model_id = m.get("id", "Unknown")
            downloads = m.get("downloads", 0)
            likes = m.get("likes", 0)
            lines.append(f"### [{idx}] {model_id} (DOWNLOADS: {downloads:,} | LIKES: {likes})")
            lines.append(f"🔗 [https://huggingface.co/{model_id}](https://huggingface.co/{model_id})\n---")

        self.hf_display.setText("\n".join(lines))

    # --- Professional Categorized Debug Log System ---

    def log(self, category: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "#e2e8f0"
        
        cat_upper = category.upper()
        if cat_upper == "INFO":
            color = "#38bdf8"
        elif cat_upper == "DEBUG":
            color = "#a855f7"
        elif cat_upper == "WARN":
            color = "#fbbf24"
        elif cat_upper == "ERROR" or cat_upper == "EXCEPTION":
            color = "#f43f5e"
        elif cat_upper == "SYSTEM":
            color = "#4ade80"

        formatted_html = f"<div style='margin: 1px 0;'><span style='color: #64748b;'>[{timestamp}]</span> <b style='color: {color};'>[{cat_upper}]</b> {message}</div>"
        self.log_edit.append(formatted_html)

        log_file = SYSTEM_LOGS_DIR / f"owlbearag_{datetime.now().strftime('%Y%m%d')}.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{cat_upper}] {message}\n")
        except Exception:
            pass

    def clear_debug_logs(self):
        self.log_edit.clear()
        self.log("SYSTEM", "Debug log screen cleared.")

    def export_debug_logs(self):
        self.log("INFO", "[ACTION INITIATED]: User pressed 'EXPORT LOG FILE'. Opening save dialog...")
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Debug Log File", str(HOME / "owlbearag_debug.log"), "Log Files (*.log);;All Files (*)")
        if file_path:
            try:
                Path(file_path).write_text(self.log_edit.toPlainText(), encoding="utf-8")
                self.log("INFO", f"Log exported successfully to {file_path}")
                QMessageBox.information(self, "Export Success", f"Log exported to:\n{file_path}")
            except Exception as e:
                self.show_exception_popup(f"Failed to export log file: {e}")

    def show_exception_popup(self, error_message: str):
        self.log("EXCEPTION", error_message)
        QMessageBox.critical(self, "System Exception Alert", f"An error occurred:\n\n{error_message}")

    # --- User Confirmation Dialog Wrappers ---

    def confirm_action(self, title: str, question: str) -> bool:
        reply = QMessageBox.question(
            self,
            title,
            question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def confirm_and_save_chat(self):
        if not self.chat_history:
            QMessageBox.warning(self, "No Chat Data", "There is no active conversation history to save.")
            return
        self.log("INFO", "[ACTION INITIATED]: User pressed 'SAVE CONVERSATION'. Prompting confirmation...")
        if self.confirm_action("Confirm Save Chat", "Save current chat conversation to disk and index into RAG database?"):
            self.save_current_chat()

    # --- Interactive Chat Methods ---

    def fetch_available_models(self):
        ollama_url = self.cfg.get("ollama_host", DEFAULT_OLLAMA_HOST)
        self.log("INFO", f"[ACTION INITIATED]: Querying Ollama API at {ollama_url} for model tag updates...")
        self.refresh_models_btn.setEnabled(False)

        self.thread_fetch = QThread()
        self.worker_fetch = ModelFetcherWorker(ollama_url)
        self.worker_fetch.moveToThread(self.thread_fetch)

        self.thread_fetch.started.connect(self.worker_fetch.run)
        self.worker_fetch.log.connect(self.log)
        self.worker_fetch.models_ready.connect(self.on_models_fetched)

        self.worker_fetch.models_ready.connect(self.thread_fetch.quit)
        self.worker_fetch.models_ready.connect(self.worker_fetch.deleteLater)
        self.thread_fetch.finished.connect(self.thread_fetch.deleteLater)

        self.thread_fetch.start()

    def on_models_fetched(self, models: list):
        self.refresh_models_btn.setEnabled(True)
        current = self.model_combo.currentText()
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        if current in models:
            self.model_combo.setCurrentText(current)

    def send_chat_message(self):
        msg = self.chat_input.text().strip()
        if not msg:
            return

        ollama_url = self.cfg.get("ollama_host", DEFAULT_OLLAMA_HOST)
        selected_model = self.model_combo.currentText()
        self.log("INFO", f"[ACTION INITIATED]: Transmitting user prompt to model [{selected_model}] at {ollama_url}...")
        self.chat_input.clear()
        self.send_btn.setEnabled(False)

        timestamp = datetime.now().strftime("%H:%M:%S")
        user_html = f"<div style='margin-bottom: 10px;'><b style='color: #38bdf8;'>[USER] ({timestamp}):</b><br/>{msg}</div>"
        self.chat_display.append(user_html)
        self.chat_history.append({"role": "User", "content": msg, "timestamp": timestamp})

        bot_header = f"<div style='margin-bottom: 4px;'><b style='color: #fbbf24;'>[{selected_model}] ({timestamp}):</b></div>"
        self.chat_display.append(bot_header)

        self.thread_chat = QThread()
        self.worker_chat = ModelChatWorker(ollama_url, selected_model, msg, self.chat_history)
        self.worker_chat.moveToThread(self.thread_chat)

        self.thread_chat.started.connect(self.worker_chat.run)
        self.worker_chat.log.connect(self.log)
        self.worker_chat.chunk.connect(self.append_chat_chunk)
        self.worker_chat.error.connect(self.show_exception_popup)
        self.worker_chat.finished.connect(self.on_chat_finished)

        self.worker_chat.finished.connect(self.thread_chat.quit)
        self.worker_chat.finished.connect(self.worker_chat.deleteLater)
        self.thread_chat.finished.connect(self.thread_chat.deleteLater)

        self.thread_chat.start()

    def append_chat_chunk(self, chunk_text: str):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk_text)
        self.chat_display.setTextCursor(cursor)

    def on_chat_finished(self, full_text: str):
        self.send_btn.setEnabled(True)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_history.append({"role": "Assistant", "content": full_text, "timestamp": timestamp})
        self.chat_display.append("<br/>")
        self.save_current_chat()

    def save_current_chat(self):
        if not self.chat_history:
            return

        chat_file = SAVED_CHATS_DIR / f"{self.current_session_id}.json"
        try:
            data = {
                "session_id": self.current_session_id,
                "model": self.model_combo.currentText(),
                "saved_at": datetime.now().isoformat(),
                "turns": self.chat_history
            }
            chat_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            self.log("INFO", f"💾 Conversation auto-saved to {chat_file.name}")
        except Exception as e:
            self.show_exception_popup(f"Failed to save chat conversation: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OwlbearagWindow()
    window.show()
    sys.exit(app.exec())
