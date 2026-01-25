---
hide:
  - navigation
  - toc
---

# Welcome to Sentinel DV

<div class="hero" markdown>

<div class="hero-content" markdown>

# 🛡️ Sentinel DV

**Verification Intelligence for AI Agents**

A security-first Model Context Protocol (MCP) server providing safe, structured, read-only access to verification artifacts from SystemVerilog/UVM/cocotb ecosystems.

[Get Started](getting-started/quick-start.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/yourusername/sentinel-dv){ .md-button }

</div>

</div>

---

## Features

<div class="grid cards" markdown>

-   :material-shield-check:{ .lg .middle } __Security First__

    ---

    Read-only by design with automatic redaction, path sandboxing, and bounded outputs. No simulator control or artifact modification.

    [:octicons-arrow-right-24: Security Model](architecture/security.md)

-   :material-file-tree:{ .lg .middle } __Schema-Driven__

    ---

    Every response conforms to versioned, typed schemas. Deterministic outputs enable reliable LLM reasoning.

    [:octicons-arrow-right-24: Schema Reference](architecture/schemas.md)

-   :material-database:{ .lg .middle } __Rich Data Access__

    ---

    Test results, UVM topology, failure analysis, assertions, coverage metrics, and regression analytics.

    [:octicons-arrow-right-24: Tool Reference](tools/overview.md)

-   :material-network:{ .lg .middle } __Simulator Agnostic__

    ---

    Works with VCS, Xcelium, Questa, Verilator, and any simulator. Adapter pattern for unified schemas.

    [:octicons-arrow-right-24: Simulator Support](guides/simulator-support.md)

-   :material-lightning-bolt:{ .lg .middle } __High Performance__

    ---

    DuckDB indexing for fast queries. Smart pagination and selective projection for efficiency.

    [:octicons-arrow-right-24: Performance Guide](guides/performance.md)

-   :material-puzzle:{ .lg .middle } __Extensible__

    ---

    Plugin architecture for custom adapters. Add support for new tools and formats easily.

    [:octicons-arrow-right-24: Adapter Development](adapters/custom.md)

</div>

---

## Quick Example

```yaml title="config.yaml"
artifact_roots:
  - /path/to/verification/regressions
  
index:
  type: duckdb
  path: ./sentinel_dv.db

adapters:
  uvm: true
  cocotb: true
  assertions: true
  coverage: true
```

```bash title="Start the server"
# Index artifacts
python -m sentinel_dv.indexing.indexer --config config.yaml --index-all

# Start MCP server
python -m sentinel_dv.server --config config.yaml
```

```text title="Query with Claude"
"Why did test axi_burst_test fail?"
→ Uses: tests.list, failures.list, assertions.failures

"Show coverage comparison between R123 and R124"
→ Uses: runs.diff, coverage.summary
```

---

## Supported Verification Frameworks

<div class="grid" markdown>

<div class="card" markdown>

### UVM (Universal Verification Methodology)

- Test topology extraction
- UVM report parsing (INFO/WARNING/ERROR/FATAL)
- Phase tracking
- Component hierarchy mapping

</div>

<div class="card" markdown>

### cocotb (Python Verification)

- JUnit/XML result parsing
- Python exception tracing
- Coroutine tracking
- Custom JSON dumps

</div>

<div class="card" markdown>

### SystemVerilog

- SVA (SystemVerilog Assertions)
- Immediate assertions
- Coverage (functional, code, toggle, FSM)
- Compile/elaboration logs

</div>

<div class="card" markdown>

### Waveforms (Experimental)

- Pre-computed summaries
- Signal toggle analysis
- Stable windows
- No raw FSDB/VCD streaming

</div>

</div>

---

## Use Cases

!!! example "Automated Triage"

    **"Why did this test fail?"**
    
    Sentinel DV provides structured failure events with categorization, evidence, and topology context.

!!! example "Regression Analytics"

    **"What changed between passing and failing runs?"**
    
    Compare runs with structured diffs: new failures, resolved issues, coverage deltas.

!!! example "Coverage Analysis"

    **"Which tests cover the AXI write channel?"**
    
    Query coverage metrics by scope, interface, and protocol.

!!! example "Assertion Mapping"

    **"Show all assertions related to the APB protocol"**
    
    Discover assertions by protocol, scope, or intent with runtime failure tracking.

---

## Installation

```bash
# From PyPI
pip install sentinel-dv

# From source
git clone https://github.com/yourusername/sentinel-dv.git
cd sentinel-dv
pip install -e ".[dev]"
```

[Full Installation Guide](getting-started/installation.md){ .md-button }

---

## Community

<div class="grid cards" markdown>

-   :fontawesome-brands-github:{ .lg .middle } __GitHub__

    ---

    Report issues, request features, contribute code

    [:octicons-arrow-right-24: yourusername/sentinel-dv](https://github.com/yourusername/sentinel-dv)

-   :material-forum:{ .lg .middle } __Discussions__

    ---

    Ask questions, share ideas, get help

    [:octicons-arrow-right-24: GitHub Discussions](https://github.com/yourusername/sentinel-dv/discussions)

-   :material-book-open:{ .lg .middle } __Documentation__

    ---

    Comprehensive guides, API reference, examples

    [:octicons-arrow-right-24: Read the Docs](https://yourusername.github.io/sentinel-dv/)

</div>

---

## License

Sentinel DV is licensed under the [Apache License 2.0](about/license.md).

---

<div class="text-center" markdown>

**Built with ❤️ for the verification community**

[Get Started →](getting-started/quick-start.md){ .md-button .md-button--primary }

</div>
