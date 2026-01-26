# Installation Guide

Complete installation instructions for Sentinel DV.

## Prerequisites

### System Requirements

**Operating Systems**:
- Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- macOS 11+ (Big Sur and later)
- Windows 10+ with WSL2

**Python**:
- Python 3.10 or later
- pip 22.0+
- virtualenv or venv (recommended)

**Hardware**:
- CPU: 2+ cores (4+ recommended for indexing)
- RAM: 4GB minimum (8GB+ recommended)
- Disk: 10GB+ free space for verification databases

---

## Installation Methods

### Method 1: pip (Recommended)

**Install from PyPI**:
```bash
pip install sentinel-dv
```

**Verify Installation**:
```bash
sentinel-dv --version
```

**Upgrade**:
```bash
pip install --upgrade sentinel-dv
```

---

### Method 2: From Source

**Clone Repository**:
```bash
git clone https://github.com/kiranreddi/sentinel-dv.git
cd sentinel-dv/backend
```

**Create Virtual Environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Install with Poetry**:
```bash
pip install poetry
poetry install
```

**Verify Installation**:
```bash
poetry run sentinel-dv --version
```

---

### Method 3: Docker

**Pull Image**:
```bash
docker pull ghcr.io/kiranreddi/sentinel-dv:latest
```

**Run Container**:
```bash
docker run -it \
  -v ./verification:/data \
  -v ./sentinel_db:/db \
  ghcr.io/kiranreddi/sentinel-dv:latest \
  sentinel-dv index --log-dir /data --output /db
```

**Docker Compose**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  sentinel-dv:
    image: ghcr.io/kiranreddi/sentinel-dv:latest
    volumes:
      - ./verification:/data:ro
      - ./sentinel_db:/db
    command: >
      sentinel-dv index
        --log-dir /data
        --output /db
        --workers 4
```

---

## MCP Server Installation

### Claude Desktop

**1. Install Sentinel DV**:
```bash
pip install sentinel-dv
```

**2. Configure Claude Desktop**:

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%/Claude/claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "sentinel-dv": {
      "command": "python",
      "args": [
        "-m",
        "sentinel_dv.server",
        "--db-path",
        "/absolute/path/to/sentinel_db"
      ]
    }
  }
}
```

**3. Restart Claude Desktop**

**4. Verify**:
Open Claude and ask: "What tools are available?"
You should see Sentinel DV tools listed.

---

### Cline (VS Code)

**1. Install Sentinel DV**:
```bash
pip install sentinel-dv
```

**2. Configure Cline**:

Edit `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "sentinel-dv": {
      "command": "python",
      "args": [
        "-m",
        "sentinel_dv.server",
        "--db-path",
        "${workspaceFolder}/sentinel_db"
      ]
    }
  }
}
```

**3. Restart VS Code**

**4. Verify**:
Ask Cline: "List failed tests from the latest run"

---

## Development Installation

### For Contributors

**1. Fork and Clone**:
```bash
git clone https://github.com/YOUR_USERNAME/sentinel-dv.git
cd sentinel-dv/backend
```

**2. Install Development Dependencies**:
```bash
poetry install --with dev,test
```

**3. Install Pre-commit Hooks**:
```bash
pre-commit install
```

**4. Run Tests**:
```bash
poetry run pytest
```

**5. Run Linters**:
```bash
poetry run ruff check .
poetry run black --check .
poetry run mypy .
```

---

### IDE Setup

**VS Code**:
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

**PyCharm**:
1. Open `backend/` directory
2. Configure Python interpreter: `.venv/bin/python`
3. Enable pytest: Settings → Tools → Python Integrated Tools → Testing → pytest
4. Enable Black formatter: Settings → Tools → External Tools

---

## Configuration

### Database Location

**Default**:
```bash
# Uses ./sentinel_db by default
sentinel-dv index --log-dir ./results
```

**Custom Location**:
```bash
sentinel-dv index --log-dir ./results --output /path/to/db
```

**Environment Variable**:
```bash
export SENTINEL_DB_PATH=/path/to/db
sentinel-dv index --log-dir ./results
```

---

### Security Settings

**Enable Path Sandboxing**:
```bash
# Only allow access to specific directories
export SENTINEL_ALLOWED_PATHS="/path/to/verification:/path/to/results"
sentinel-dv server --db-path ./sentinel_db
```

**Disable Redaction** (not recommended):
```bash
export SENTINEL_DISABLE_REDACTION=true
sentinel-dv server --db-path ./sentinel_db
```

---

### Performance Settings

**Worker Threads**:
```bash
# Use 8 parallel workers for indexing
sentinel-dv index --log-dir ./results --workers 8
```

**Memory Limit**:
```bash
# Limit memory usage to 4GB
export SENTINEL_MAX_MEMORY_MB=4096
sentinel-dv index --log-dir ./results
```

---

## Verification

### Test Installation

**1. Index Sample Data**:
```bash
# Download sample verification data
curl -O https://github.com/kiranreddi/sentinel-dv/releases/download/v1.0.0/sample_data.tar.gz
tar -xzf sample_data.tar.gz

# Index the sample data
sentinel-dv index \
  --log-dir ./sample_data \
  --run-id SAMPLE_RUN \
  --output ./sentinel_db
```

**2. Query Data**:
```bash
# List indexed runs
sentinel-dv query runs.list --output json

# List tests
sentinel-dv query tests.list --run-id SAMPLE_RUN --output json
```

**3. Start MCP Server**:
```bash
sentinel-dv server --db-path ./sentinel_db
```

---

## Troubleshooting

### Installation Issues

**Problem**: `pip install sentinel-dv` fails
```
ERROR: Could not find a version that satisfies the requirement sentinel-dv
```

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Try again
pip install sentinel-dv
```

---

**Problem**: Poetry install fails
```
ERROR: No module named 'poetry'
```

**Solution**:
```bash
pip install poetry
poetry install
```

---

**Problem**: Import error
```python
ModuleNotFoundError: No module named 'sentinel_dv'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall
pip install -e .
```

---

### MCP Server Issues

**Problem**: Claude Desktop doesn't see Sentinel DV

**Solution**:
1. Check `claude_desktop_config.json` syntax (valid JSON)
2. Use absolute paths (no `~` or `${HOME}`)
3. Restart Claude Desktop completely
4. Check logs: `~/Library/Logs/Claude/mcp.log`

---

**Problem**: Permission denied
```
PermissionError: [Errno 13] Permission denied: '/path/to/sentinel_db'
```

**Solution**:
```bash
# Fix permissions
chmod -R 755 ./sentinel_db

# Or use a writable location
sentinel-dv server --db-path ~/sentinel_db
```

---

### Database Issues

**Problem**: Database locked
```
sqlite3.OperationalError: database is locked
```

**Solution**:
```bash
# Close all connections
pkill -f sentinel-dv

# Or use WAL mode (recommended)
export SQLITE_JOURNAL_MODE=WAL
sentinel-dv server --db-path ./sentinel_db
```

---

**Problem**: Database corrupted
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution**:
```bash
# Backup and rebuild
mv sentinel_db sentinel_db.bak
sentinel-dv index --log-dir ./results --output ./sentinel_db
```

---

## Platform-Specific Notes

### Linux

**Dependencies**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

---

### macOS

**Dependencies**:
```bash
# Using Homebrew
brew install python@3.11

# Verify
python3 --version
```

---

### Windows

**Using WSL2** (recommended):
```bash
# Install WSL2
wsl --install

# Inside WSL2
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
pip3 install sentinel-dv
```

**Using Native Python**:
```powershell
# Install Python from python.org
# Then in PowerShell:
pip install sentinel-dv
```

---

## Uninstallation

### Remove Package

```bash
pip uninstall sentinel-dv
```

### Remove Database

```bash
rm -rf ./sentinel_db
```

### Remove Configuration

```bash
# Claude Desktop
rm ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Cline
rm .vscode/mcp.json
```

---

## Next Steps

- [Quick Start →](quick-start.md) - Begin using Sentinel DV
- [Configuration →](../architecture/overview.md) - Advanced configuration
- [MCP Tools →](../tools/overview.md) - Available tools reference
