# Schema Reference

All Sentinel DV responses conform to versioned, typed schemas for reliable LLM reasoning.

## Schema Versioning

Every response includes a `schema_version` field:

```json
{
  "schema_version": "1.0.0",
  "data": {...}
}
```

**Version Format**: `MAJOR.MINOR.PATCH` (semver)
- **MAJOR**: Breaking changes (field removals, type changes)
- **MINOR**: Additive changes (new fields, new enum values)
- **PATCH**: Bug fixes (no schema impact)

## Core Schemas

### RunRef

Reference to a verification run.

```python
class RunRef(BaseModel):
    run_id: str
    run_id_full: str | None = None
    suite: str | None = None
    created_at: str | None = None  # RFC3339 timestamp
```

**Example**:
```json
{
  "run_id": "R20260125_143000",
  "run_id_full": "R20260125_143000_NIGHTLY_GH12345",
  "suite": "nightly",
  "created_at": "2026-01-25T14:30:00Z"
}
```

### TestCase

Complete test result information.

```python
class TestCase(BaseModel):
    id: str  # T20260125_143000_test_name
    framework: Framework  # "uvm" | "cocotb" | "sv_unit" | "unknown"
    name: str
    seed: int | None = None
    simulator: SimulatorInfo | None = None
    dut: DutInfo | None = None
    status: TestStatus  # "pass" | "fail" | "error" | "skipped" | "unknown"
    duration_ms: int | None = None
    run: RunRef
    evidence: list[EvidenceRef] = []
```

**Example**:
```json
{
  "id": "T20260125_143000_axi_burst_test",
  "framework": "uvm",
  "name": "axi_burst_test",
  "seed": 42,
  "simulator": {
    "vendor": "VCS",
    "version": "2023.12"
  },
  "dut": {
    "top": "axi_interconnect",
    "config": {"NUM_MASTERS": "4", "DATA_WIDTH": "64"}
  },
  "status": "fail",
  "duration_ms": 15420,
  "run": {
    "run_id": "R20260125_143000",
    "suite": "nightly"
  },
  "evidence": [
    {
      "kind": "log",
      "path": "axi_burst_test.log",
      "span": {"start_line": 1, "end_line": 450}
    }
  ]
}
```

### FailureEvent

Categorized failure information.

```python
class FailureEvent(BaseModel):
    id: str | None = None  # F20260125_143000_001
    test_id: str | None = None
    severity: Severity  # "info" | "warning" | "error" | "fatal"
    category: Category  # "assertion" | "scoreboard" | "protocol" | ...
    summary: str
    message: str
    time_ns: int | None = None
    phase: str | None = None
    component: str | None = None
    tags: list[str] = []
    evidence: list[EvidenceRef] = []
```

**Categories**:
- `assertion`: Assertion failures (SVA, PSL, etc.)
- `scoreboard`: Data mismatch in checkers
- `protocol`: Protocol violations (AXI, PCIe, etc.)
- `timeout`: Timeout errors
- `syntax`: Compilation/syntax errors
- `configuration`: Configuration issues
- `resource`: Resource exhaustion
- `unknown`: Uncategorized

**Example**:
```json
{
  "id": "F20260125_143000_001",
  "test_id": "T20260125_143000_axi_burst_test",
  "severity": "error",
  "category": "scoreboard",
  "summary": "DATA MISMATCH: Expected 0xDEAD, Got 0xBEEF",
  "message": "Scoreboard check failed at address 0x1000...",
  "time_ns": 100000,
  "phase": "main_phase",
  "component": "uvm_test_top.env.scoreboard",
  "tags": ["scoreboard", "data-integrity", "write-path"],
  "evidence": [
    {
      "kind": "log",
      "path": "axi_burst_test.log",
      "span": {"start_line": 234, "end_line": 234},
      "extract": "UVM_ERROR @ 100 ns: DATA MISMATCH..."
    }
  ]
}
```

### TestTopology

Test hierarchy and interface bindings.

```python
class TestTopology(BaseModel):
    test_id: str
    uvm: UvmTopology | None = None
    interfaces: list[InterfaceBinding] = []

class UvmTopology(BaseModel):
    test_class: str
    envs: list[UvmComponent] = []
    agents: list[UvmComponent] = []
    scoreboards: list[UvmComponent] = []
    sequencers: list[UvmComponent] = []
    drivers: list[UvmComponent] = []
    monitors: list[UvmComponent] = []

class InterfaceBinding(BaseModel):
    name: str  # e.g., "axi_m0"
    protocol: Protocol  # "AXI4" | "PCIe" | "USB" | ...
    direction: Direction  # "master" | "slave" | "monitor"
    signals: SignalInfo | None = None
    endpoints: EndpointInfo | None = None
```

**Example**:
```json
{
  "test_id": "T20260125_143000_axi_burst_test",
  "uvm": {
    "test_class": "axi_burst_test",
    "envs": [
      {
        "path": "uvm_test_top.env",
        "type": "axi_env",
        "role": "env"
      }
    ],
    "agents": [
      {
        "path": "uvm_test_top.env.master_agent",
        "type": "axi_master_agent",
        "role": "agent"
      }
    ],
    "scoreboards": [
      {
        "path": "uvm_test_top.env.scoreboard",
        "type": "axi_scoreboard",
        "role": "scoreboard"
      }
    ]
  },
  "interfaces": [
    {
      "name": "axi_m0",
      "protocol": "AXI4",
      "direction": "master",
      "signals": {
        "clk": "aclk",
        "rst": "aresetn"
      },
      "endpoints": {
        "driver": "uvm_test_top.env.master_agent.driver",
        "monitor": "uvm_test_top.env.master_agent.monitor"
      }
    }
  ]
}
```

### CoverageSummary

Coverage metrics with missed bins.

```python
class CoverageSummary(BaseModel):
    run_id: str
    kind: CoverageKind  # "functional" | "code" | "assertion"
    scope: str | None = None
    overall_percentage: float
    coverpoints: list[CoverPoint] = []
    missed_bins: list[MissedBin] = []

class CoverPoint(BaseModel):
    name: str
    percentage: float
    hits: int
    bins_total: int
    bins_covered: int

class MissedBin(BaseModel):
    coverpoint: str
    bin_name: str
    expected_hits: int
    actual_hits: int
```

**Example**:
```json
{
  "run_id": "R20260125_143000",
  "kind": "functional",
  "scope": "axi_burst_test",
  "overall_percentage": 87.5,
  "coverpoints": [
    {
      "name": "axi_transaction.burst_type",
      "percentage": 100.0,
      "hits": 450,
      "bins_total": 4,
      "bins_covered": 4
    },
    {
      "name": "axi_transaction.burst_len",
      "percentage": 75.0,
      "hits": 320,
      "bins_total": 16,
      "bins_covered": 12
    }
  ],
  "missed_bins": [
    {
      "coverpoint": "axi_transaction.burst_len",
      "bin_name": "burst_len[12-15]",
      "expected_hits": 10,
      "actual_hits": 0
    }
  ]
}
```

### EvidenceRef

Reference to supporting evidence (logs, waveforms, etc.).

```python
class EvidenceRef(BaseModel):
    kind: EvidenceKind  # "log" | "waveform" | "coverage" | "artifact"
    path: str  # Relative path, validated
    span: TimeSpan | None = None
    extract: str | None = None
    hash: str | None = None

class TimeSpan(BaseModel):
    # Line-based span
    start_line: int | None = Field(None, ge=1)
    end_line: int | None = Field(None, ge=1)
    
    # Time-based span
    start_ns: int | None = Field(None, ge=0)
    end_ns: int | None = Field(None, ge=0)
```

**Example**:
```json
{
  "kind": "log",
  "path": "sim_results/axi_burst_test.log",
  "span": {
    "start_line": 234,
    "end_line": 250
  },
  "extract": "UVM_ERROR @ 100 ns: (scoreboard) DATA MISMATCH...",
  "hash": "sha256:abc123..."
}
```

## Response Wrappers

All list tools return paginated responses:

```python
class PaginatedResponse(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[T]  # Generic
```

**Example**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 50,
  "total_items": 150,
  "total_pages": 3,
  "items": [...]
}
```

## Type Definitions

### Enums (Literal Types)

```python
# Framework
Framework = Literal["uvm", "cocotb", "sv_unit", "unknown"]

# Test status
TestStatus = Literal["pass", "fail", "error", "skipped", "unknown"]

# Severity
Severity = Literal["info", "warning", "error", "fatal"]

# Failure category
Category = Literal[
    "assertion", "scoreboard", "protocol", "timeout",
    "syntax", "configuration", "resource", "unknown"
]

# Protocol
Protocol = Literal[
    "AXI4", "AXI3", "AHB", "APB", "PCIe", "USB",
    "Ethernet", "I2C", "SPI", "UART", "CAN", "unknown"
]

# Coverage kind
CoverageKind = Literal["functional", "code", "assertion"]

# Evidence kind
EvidenceKind = Literal["log", "waveform", "coverage", "artifact"]
```

## Schema Evolution

### Adding Fields (Minor Version)

**Before** (1.0.0):
```python
class TestCase(BaseModel):
    id: str
    name: str
    status: TestStatus
```

**After** (1.1.0):
```python
class TestCase(BaseModel):
    id: str
    name: str
    status: TestStatus
    duration_ms: int | None = None  # New optional field
```

**Impact**: No breaking change, clients ignore unknown fields.

### Changing Types (Major Version)

**Before** (1.0.0):
```python
class TestCase(BaseModel):
    duration: float  # seconds
```

**After** (2.0.0):
```python
class TestCase(BaseModel):
    duration_ms: int  # milliseconds
```

**Impact**: Breaking change, requires migration.

### Removing Fields (Major Version)

**Before** (1.0.0):
```python
class TestCase(BaseModel):
    deprecated_field: str
```

**After** (2.0.0):
```python
class TestCase(BaseModel):
    # deprecated_field removed
    pass
```

**Impact**: Breaking change, requires migration.

## Validation Rules

All schemas enforce validation:

```python
# IDs must match patterns
run_id: str = Field(..., pattern=r"^R\d{8}_\d{6}")

# Percentages must be 0-100
percentage: float = Field(..., ge=0, le=100)

# Positive integers
duration_ms: int = Field(..., ge=0)

# Non-empty strings
name: str = Field(..., min_length=1)

# Relative paths only
path: str = Field(..., pattern=r"^[^/].*")  # No leading /
```

## Best Practices

### For Clients

1. **Check schema_version**
   ```python
   response = client.call("tests.get", {...})
   if response["schema_version"] != "1.0.0":
       warn("Schema version mismatch")
   ```

2. **Handle Optional Fields**
   ```python
   test = response["data"]
   duration = test.get("duration_ms", 0)  # Default if missing
   ```

3. **Validate Enums**
   ```python
   if test["status"] not in ["pass", "fail", "error", "skipped", "unknown"]:
       warn("Unknown status value")
   ```

### For Server Developers

1. **Always Set Defaults**
   ```python
   class TestCase(BaseModel):
       tags: list[str] = []  # Not None
   ```

2. **Use Literal Types**
   ```python
   status: Literal["pass", "fail"]  # Not str
   ```

3. **Add Validation**
   ```python
   percentage: float = Field(..., ge=0, le=100)
   ```

## Schema Files

All schemas defined in:
- `sentinel_dv/schemas/common.py` - Shared types
- `sentinel_dv/schemas/tests.py` - Test schemas
- `sentinel_dv/schemas/failures.py` - Failure schemas
- `sentinel_dv/schemas/coverage.py` - Coverage schemas

## Migration Guide

When schemas change, we provide migration docs:

**1.0.0 → 2.0.0 Migration**:
```python
# Old (1.0.0)
test = {
    "duration": 15.42  # seconds
}

# New (2.0.0)
test = {
    "duration_ms": 15420  # milliseconds
}

# Migration
duration_ms = int(old_duration * 1000)
```
