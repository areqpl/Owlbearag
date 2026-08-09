# 🔐 Security & Configuration Reference

## Overview
All secrets, SSH key locations, and endpoint URLs are saved securely at `~/.gemini/antigravity-cli/config.json`.

## Permission Enforcement
The `ConfigSecurityManager` automatically enforces mode `0600` owner-only permissions on launch to prevent unauthorized local reading.
