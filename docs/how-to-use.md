# How to Use Sentinel DV - Complete Guide

Welcome to Sentinel DV! This guide will help you effectively use the MCP server for verification intelligence.

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Setting Up Your Environment](#setting-up-your-environment)
4. [Indexing Verification Artifacts](#indexing-verification-artifacts)
5. [Using MCP Tools](#using-mcp-tools)
6. [Integration with AI Agents](#integration-with-ai-agents)
7. [Common Workflows](#common-workflows)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Quick Start

### Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/kiranreddi/sentinel-dv.git
cd sentinel-dv

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Verify installation
python -m sentinel_dv.server --help
```

### First Index (10 minutes)

```bash
# 1. Create configuration
cp config.example.yaml config.yaml

# 2. Edit config.yaml to point to your artifacts
nano config.yaml
# Set artifact_roots to your verification directories

# 3. Index demo artifacts (test the system)
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --artifacts demo/

# 4. Check index was created
ls -lh sentinel.duckdb
```

### Start Server (2 minutes)

```bash
# Start the MCP server
python -m sentinel_dv.server --config config.yaml

# Server is now ready for MCP clients!
```

---

## Understanding the Architecture

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                   MCP Client                        │
│            (Claude, Custom Agent, etc.)             │
└────────────────┬────────────────────────────────────┘
                 │ MCP Protocol
┌────────────────▼────────────────────────────────────┐
│              Sentinel DV Server                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  MCP Tools (runs, tests, failures, etc.)     │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│  ┌──────────────▼───────────────────────────────┐  │
│  │      DuckDB Index Store                      │  │
│  │  - runs, tests, failures, coverage           │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│  ┌──────────────▼───────────────────────────────┐  │
│  │  Adapters (UVM, cocotb, coverage)            │  │
│  └──────────────┬───────────────────────────────┘  │
└─────────────────┼────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│         Verification Artifacts                       │
│  - UVM logs                                          │
│  - cocotb JUnit XML                                  │
│  - Coverage reports                                  │
│  - Assertion definitions                             │
└──────────────────────────────────────────────────────┘
```

### Data Flow

1. **Indexing Phase** (offline)
   - Adapters parse raw artifacts
   - Data is normalized and classified
   - IDs are generated deterministically
   - Everything stored in DuckDB

2. **Query Phase** (runtime)
   - MCP client sends tool request
   - Server queries DuckDB index
   - Results are paginated and returned
   - All responses are typed and validated

---

## Setting Up Your Environment

### Configuration File Explained

```yaml
# config.yaml - Complete reference

# 1. ARTIFACT ROOTS (Required)
# Where your verification artifacts are located
artifact_roots:
  - /path/to/nightly/regressions
  - /path/to/continuous/integration
  - ~/verification/runs

# 2. INDEX CONFIGURATION
index:
  # Database path (created if doesn't exist)
  db_path: "./sentinel.duckdb"
  
  # Incremental indexing (skip unchanged files)
  incremental: true
  
  # Indexing parallelism
  workers: 4

# 3. ADAPTER CONFIGURATION
adapters:
  # Enable/disable adapters
  enabled:
    - uvm
    - cocotb
    - coverage
    - assertions
    - regression_analytics
  
  # Adapter-specific settings
  uvm:
    # Vendor-specific parsing
    vendors:
      - questa
      - vcs
      - xcelium
    
    # Extract topology information
    extract_topology: true
  
  cocotb:
    # JUnit XML locations
    result_patterns:
      - "**/results.xml"
      - "**/cocotb_results.xml"
  
  coverage:
    # Vendor coverage formats
    formats:
      - questa_ucdb
      - vcs_coverage
      - xcelium_cov

# 4. SECURITY SETTINGS
security:
  # Maximum response size (bytes)
  max_response_bytes: 2097152  # 2MB
  
  # Maximum page size for pagination
  max_page_size: 200
  
  # Maximum evidence references per response
  max_evidence_refs: 10
  
  # Maximum excerpt length
  max_excerpt_length: 1024

# 5. REDACTION (PII/Credentials)
redaction:
  enabled: true
  
  # Automatic patterns
  redact_emails: true
  redact_paths: true
  redact_ips: true
  redact_credentials: true
  
  # Custom patterns (regex)
  custom_patterns:
    - 'SECRET_\w+'
    - 'API_KEY_\w+'

# 6. TAXONOMY CUSTOMIZATION
taxonomy:
  # Custom failure categories
  custom_categories:
    - custom_protocol_x
  
  # Custom tags
  custom_tags:
    - my_company_protocol

# 7. PERFORMANCE TUNING
performance:
  # Query cache size
  cache_size_mb: 100
  
  # DuckDB threads
  duckdb_threads: 4
  
  # Connection pool
  max_connections: 10
```

### Directory Structure

Organize your artifacts like this:

```
verification/
├── nightly_runs/
│   ├── 2026-01-20/
│   │   ├── run_123/
│   │   │   ├── test_axi_burst.log
│   │   │   ├── coverage.xml
│   │   │   └── assertions.rpt
│   │   └── run_124/
│   └── 2026-01-21/
├── continuous_integration/
│   └── pr_456/
│       ├── cocotb_results.xml
│       └── uvm_test.log
└── regression_database/
    └── historical_data.db
```

---

## Indexing Verification Artifacts

### Full Indexing

```bash
# Index all configured artifact roots
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --index-all

# Expected output:
# Scanning artifacts...
# Found 1,234 files
# Parsing UVM logs: 500 files
# Parsing cocotb results: 234 files
# Parsing coverage: 500 files
# Generating IDs...
# Writing to DuckDB...
# Indexed 1,234 files in 45.3s
# Runs: 50
# Tests: 2,500
# Failures: 156
# Coverage summaries: 50
```

### Incremental Indexing

```bash
# Only index new/changed files
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --incremental

# Much faster for daily updates!
```

### Selective Indexing

```bash
# Index specific directory
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --artifacts /path/to/specific/run

# Index with filters
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --suite nightly \
    --from-date 2026-01-20
```

### Monitoring Progress

```bash
# With verbose output
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --index-all \
    --verbose

# With progress bar
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --index-all \
    --progress

# Dry run (see what would be indexed)
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --index-all \
    --dry-run
```

---

## Using MCP Tools

### Available Tools

Sentinel DV provides 14 MCP tools across 5 categories:

#### 1. Discovery Tools

**runs.list** - List available test runs
```json
{
  "suite": "nightly",
  "page": 1,
  "page_size": 50
}
```

**tests.list** - List tests with filters
```json
{
  "run_id": "r_abc123",
  "status": "fail",
  "framework": "uvm"
}
```

**failures.list** - List failures
```json
{
  "run_id": "r_abc123",
  "category": "assertion",
  "severity": "error"
}
```

#### 2. Detail Tools

**runs.get** - Get run details
```json
{
  "run_id": "r_abc123"
}
```

**tests.get** - Get test details with topology
```json
{
  "test_id": "t_def456"
}
```

**failures.get** - Get failure details
```json
{
  "failure_id": "f_ghi789"
}
```

#### 3. Analysis Tools

**regressions.summary** - Get regression analytics
```json
{
  "suite": "nightly",
  "window_days": 7
}
```

**runs.diff** - Compare two runs
```json
{
  "base_run_id": "r_abc123",
  "compare_run_id": "r_def456"
}
```

**flaky_tests.detect** - Identify flaky tests
```json
{
  "suite": "nightly",
  "window_days": 30,
  "min_runs": 10
}
```

#### 4. Coverage Tools

**coverage.summary** - Get coverage metrics
```json
{
  "run_id": "r_abc123",
  "kind": "functional"
}
```

**coverage.diff** - Compare coverage
```json
{
  "base_run_id": "r_abc123",
  "compare_run_id": "r_def456"
}
```

#### 5. Assertion Tools

**assertions.list** - List assertion definitions
```json
{
  "scope": "axi_agent",
  "intent_protocol": "axi4"
}
```

**assertions.failures** - Get assertion failures
```json
{
  "run_id": "r_abc123",
  "assertion_id": "a_jkl012"
}
```

---

## Integration with AI Agents

### Claude Desktop Integration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sentinel-dv": {
      "command": "python",
      "args": [
        "-m",
        "sentinel_dv.server",
        "--config",
        "/full/path/to/config.yaml"
      ],
      "env": {
        "PYTHONPATH": "/full/path/to/sentinel-dv"
      }
    }
  }
}
```

Restart Claude Desktop, and Sentinel DV tools will be available!

### Custom MCP Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def query_sentinel_dv():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "sentinel_dv.server", "--config", "config.yaml"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List failing tests
            result = await session.call_tool("tests_list", {
                "status": "fail",
                "page": 1,
                "page_size": 10
            })
            
            print(result)
```

### API Client (HTTP/REST)

```python
import requests

# Sentinel DV can optionally expose HTTP API
response = requests.post("http://localhost:8000/mcp/tools/tests_list", json={
    "status": "fail",
    "page": 1
})

tests = response.json()
```

---

## Common Workflows

### Workflow 1: Daily Regression Triage

```bash
# 1. Index latest nightly run
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --artifacts /nightly/2026-01-25 \
    --suite nightly

# 2. Start server
python -m sentinel_dv.server --config config.yaml
```

Then in Claude:

```
"Show me the regression summary for the nightly suite from the past 7 days"
→ Uses: regressions.summary

"List all assertion failures from last night's run"
→ Uses: failures.list with category=assertion

"Compare coverage between yesterday and today"
→ Uses: runs.diff
```

### Workflow 2: PR Validation

```bash
# Index PR artifacts
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --artifacts /ci/pr_123 \
    --suite pr_validation
```

In Claude:

```
"Did PR #123 introduce any new failures?"
→ Uses: runs.diff comparing main vs PR

"What's the coverage impact of this PR?"
→ Uses: coverage.diff
```

### Workflow 3: Flaky Test Detection

```bash
# Index historical data
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --artifacts /historical/past_30_days \
    --suite nightly
```

In Claude:

```
"Which tests are flaky in the nightly suite?"
→ Uses: flaky_tests.detect

"Show me tests that fail <20% of the time"
→ Uses: flaky_tests.detect with threshold=0.2
```

### Workflow 4: Root Cause Analysis

In Claude:

```
"Why did test axi_burst_wr fail?"
→ Uses: tests.get, failures.list

"Show me the scoreboard mismatches in the AXI agent"
→ Uses: failures.list with component=axi_agent, category=scoreboard

"What assertions failed during this test?"
→ Uses: assertions.failures
```

---

## Troubleshooting

### Issue: Indexing is slow

**Solution:**
```yaml
# In config.yaml, increase parallelism
index:
  workers: 8  # Use more CPU cores

performance:
  duckdb_threads: 8
```

### Issue: Server won't start

**Check:**
```bash
# 1. Verify Python version
python --version  # Must be 3.10+

# 2. Check dependencies
pip list | grep fastmcp
pip list | grep duckdb

# 3. Verify config
python -c "from sentinel_dv.config import load_config; load_config('config.yaml')"

# 4. Check database
ls -lh sentinel.duckdb
```

### Issue: No results from queries

**Debug:**
```bash
# 1. Check index contents
python -c "
from sentinel_dv.indexing.store import IndexStore
with IndexStore('sentinel.duckdb') as store:
    print(f'Runs: {store.count_runs()}')
    print(f'Tests: {store.count_tests()}')
    print(f'Failures: {store.count_failures()}')
"

# 2. Re-index with verbose logging
python -m sentinel_dv.indexing.indexer \
    --config config.yaml \
    --index-all \
    --verbose \
    --log-level DEBUG
```

### Issue: Redaction too aggressive

**Solution:**
```yaml
# In config.yaml, tune redaction
redaction:
  enabled: true
  redact_emails: false  # Keep emails if needed
  redact_paths: false   # Keep paths if needed
  
  # Remove aggressive patterns
  custom_patterns: []
```

### Issue: MCP client can't connect

**Check:**
```bash
# 1. Test server manually
python -m sentinel_dv.server --config config.yaml

# 2. Check server logs
python -m sentinel_dv.server --config config.yaml --log-level DEBUG

# 3. Verify MCP protocol version
python -c "import fastmcp; print(fastmcp.__version__)"
```

---

## Best Practices

### 1. Regular Indexing

Schedule daily indexing:

```bash
# crontab -e
0 2 * * * cd /path/to/sentinel-dv && python -m sentinel_dv.indexing.indexer --config config.yaml --incremental --suite nightly
```

### 2. Organize Artifacts

Keep artifacts organized by suite/date:

```
/verification/
├── nightly/YYYY-MM-DD/
├── pr/PR_NUMBER/
└── release/VERSION/
```

### 3. Use Incremental Indexing

```bash
# Daily: incremental (fast)
python -m sentinel_dv.indexing.indexer --config config.yaml --incremental

# Weekly: full re-index (ensures consistency)
python -m sentinel_dv.indexing.indexer --config config.yaml --index-all
```

### 4. Monitor Index Size

```bash
# Check database size
du -h sentinel.duckdb

# Vacuum if needed (reclaim space)
python -c "
from sentinel_dv.indexing.store import IndexStore
with IndexStore('sentinel.duckdb') as store:
    store._conn.execute('VACUUM')
"
```

### 5. Version Control Config

```bash
# Track config changes
git add config.yaml
git commit -m "Update artifact roots"
git push
```

### 6. Security Checklist

- ✅ Enable redaction for production
- ✅ Restrict artifact_roots to necessary paths
- ✅ Set appropriate max_response_bytes
- ✅ Review custom_patterns for your environment
- ✅ Never commit credentials in config.yaml

### 7. Performance Tuning

```yaml
# For large scale (100K+ tests)
index:
  workers: 16
  
performance:
  cache_size_mb: 500
  duckdb_threads: 16
  max_connections: 20

# For small scale (<10K tests)
index:
  workers: 4
  
performance:
  cache_size_mb: 50
  duckdb_threads: 4
  max_connections: 5
```

---

## Advanced Usage

### Custom Taxonomy

```yaml
# In config.yaml
taxonomy:
  custom_categories:
    - custom_axi_protocol_violation
    - custom_ahb_timeout
  
  custom_tags:
    - my_dut_version_1_0
    - my_protocol_xyz
```

### Programmatic Access

```python
from sentinel_dv.indexing.store import IndexStore
from sentinel_dv.adapters import UVMLogParser

# Direct adapter usage
parser = UVMLogParser()
result = parser.parse_log("test.log")

# Direct store access
with IndexStore("sentinel.duckdb") as store:
    tests, total = store.query_tests(
        status="fail",
        framework="uvm"
    )
    
    for test in tests:
        print(f"{test['name']}: {test['status']}")
```

### Custom Adapters

```python
# Create custom adapter for your tool
from sentinel_dv.adapters.base import BaseAdapter

class MyToolAdapter(BaseAdapter):
    def parse(self, file_path):
        # Your parsing logic
        return {
            "tests": [...],
            "failures": [...]
        }

# Register adapter
# In config.yaml:
adapters:
  enabled:
    - my_tool
  
  my_tool:
    patterns:
      - "**/*.mytool"
```

---

## Getting Help

### Resources

- 📖 [Full Documentation](https://kiranreddi.github.io/sentinel-dv/)
- 💬 [GitHub Discussions](https://github.com/kiranreddi/sentinel-dv/discussions)
- 🐛 [Issue Tracker](https://github.com/kiranreddi/sentinel-dv/issues)
- 📧 Email: support@sentinel-dv.io

### Community

- Join our Discord: [discord.gg/sentinel-dv](#)
- Follow updates: [@SentinelDV](#)
- Weekly office hours: Wednesdays 2pm PST

---

## Next Steps

1. ✅ Complete quick start
2. ✅ Index your first artifacts
3. ✅ Try example queries in Claude
4. 📖 Read [Architecture Overview](architecture/overview.md)
5. 🔧 Explore [Tool Reference](tools/overview.md)
6. 🚀 Set up production deployment

**Happy debugging! 🛡️**
