# Analysis Tools

Analyze failure patterns, assertion violations, and coverage metrics.

## failures.list

List all failure events from verification runs.

### Purpose
Search and filter failures by category, severity, assertion, and time range.

### Input Schema

```python
class FailuresListInput(BaseModel):
    run_id: str | None = None
    test_id: str | None = None
    category: Category | None = None  # "protocol" | "functional" | "timing" | "power"
    severity: Severity | None = None  # "error" | "warning" | "fatal"
    assertion_name: str | None = None
    assertion_scope: str | None = None
    min_time_ns: int | None = None
    max_time_ns: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: Literal["time_ns", "severity"] = "time_ns"
    sort_order: Literal["asc", "desc"] = "asc"
```

### Output Schema

```python
class FailuresListOutput(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[FailureEvent]

class FailureEvent(BaseModel):
    test_id: str
    assertion_name: str
    assertion_scope: str
    category: str
    severity: str
    time_ns: int
    message: str
    context: dict[str, Any]
```

### Example

**Query**:
```json
{
  "run_id": "R20260125_143000",
  "category": "protocol",
  "severity": "error"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 50,
  "total_items": 5,
  "total_pages": 1,
  "items": [
    {
      "test_id": "T20260125_143000_axi_burst_test",
      "assertion_name": "axi_awvalid_awready_check",
      "assertion_scope": "axi_master_if",
      "category": "protocol",
      "severity": "error",
      "time_ns": 12450,
      "message": "AWVALID deasserted before AWREADY handshake",
      "context": {
        "awvalid": "0",
        "awready": "0",
        "awaddr": "0x1000"
      }
    },
    {
      "test_id": "T20260125_143000_axi_burst_test",
      "assertion_name": "axi_wvalid_wready_check",
      "assertion_scope": "axi_master_if",
      "category": "protocol",
      "severity": "error",
      "time_ns": 14200,
      "message": "WVALID deasserted before WREADY handshake",
      "context": {
        "wvalid": "0",
        "wready": "0",
        "wdata": "0xdeadbeef"
      }
    }
  ]
}
```

---

## assertions.failures

Get failure statistics for a specific assertion.

### Purpose
Analyze how often and where an assertion fires across tests.

### Input Schema

```python
class AssertionsFailuresInput(BaseModel):
    name: str
    scope: str
    run_id: str | None = None
```

### Output Schema

```python
class AssertionsFailuresOutput(BaseModel):
    schema_version: str = "1.0.0"
    item: AssertionFailureStats

class AssertionFailureStats(BaseModel):
    name: str
    scope: str
    total_firings: int
    affected_tests: int
    failure_events: list[FailureEvent]
    common_contexts: list[dict[str, Any]]
```

### Example

**Query**:
```json
{
  "name": "axi_awvalid_awready_check",
  "scope": "axi_master_if",
  "run_id": "R20260125_143000"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "item": {
    "name": "axi_awvalid_awready_check",
    "scope": "axi_master_if",
    "total_firings": 12,
    "affected_tests": 3,
    "failure_events": [
      {
        "test_id": "T20260125_143000_axi_burst_test",
        "assertion_name": "axi_awvalid_awready_check",
        "assertion_scope": "axi_master_if",
        "category": "protocol",
        "severity": "error",
        "time_ns": 12450,
        "message": "AWVALID deasserted before AWREADY handshake",
        "context": {
          "awvalid": "0",
          "awready": "0",
          "awaddr": "0x1000"
        }
      }
    ],
    "common_contexts": [
      {
        "awvalid": "0",
        "awready": "0",
        "pattern": "early_deassert"
      }
    ]
  }
}
```

---

## coverage.summary

Get aggregated coverage statistics.

### Purpose
Analyze coverage metrics across runs, kinds, and scopes.

### Input Schema

```python
class CoverageSummaryInput(BaseModel):
    run_id: str
    kind: CoverageKind | None = None  # "functional" | "code" | "assertion"
    scope: str | None = None
```

### Output Schema

```python
class CoverageSummaryOutput(BaseModel):
    schema_version: str = "1.0.0"
    item: CoverageSummary

class CoverageSummary(BaseModel):
    run_id: str
    overall_percentage: float
    by_kind: dict[str, KindCoverage]
    by_scope: dict[str, ScopeCoverage]

class KindCoverage(BaseModel):
    kind: str
    percentage: float
    bins_total: int
    bins_covered: int

class ScopeCoverage(BaseModel):
    scope: str
    percentage: float
    bins_total: int
    bins_covered: int
```

### Example

**Query**:
```json
{
  "run_id": "R20260125_143000"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "item": {
    "run_id": "R20260125_143000",
    "overall_percentage": 85.7,
    "by_kind": {
      "functional": {
        "kind": "functional",
        "percentage": 87.5,
        "bins_total": 120,
        "bins_covered": 105
      },
      "code": {
        "kind": "code",
        "percentage": 92.3,
        "bins_total": 500,
        "bins_covered": 461
      },
      "assertion": {
        "kind": "assertion",
        "percentage": 78.0,
        "bins_total": 50,
        "bins_covered": 39
      }
    },
    "by_scope": {
      "axi_burst_test": {
        "scope": "axi_burst_test",
        "percentage": 87.5,
        "bins_total": 120,
        "bins_covered": 105
      },
      "axi_protocol_test": {
        "scope": "axi_protocol_test",
        "percentage": 82.3,
        "bins_total": 96,
        "bins_covered": 79
      }
    }
  }
}
```

---

## Common Patterns

### Failure Analysis Workflow

**1. List Failures by Severity**
```json
{
  "run_id": "R20260125_143000",
  "severity": "error",
  "sort_by": "time_ns"
}
```

**2. Group by Assertion**
```python
failures = client.failures.list(run_id="...")
by_assertion = {}
for f in failures.items:
    key = (f.assertion_name, f.assertion_scope)
    by_assertion.setdefault(key, []).append(f)
```

**3. Analyze Each Assertion**
```python
for (name, scope), events in by_assertion.items():
    stats = client.assertions.failures(name=name, scope=scope)
    print(f"{name}: {stats.total_firings} firings, {stats.affected_tests} tests")
```

### Coverage Analysis Workflow

**1. Get Overall Summary**
```json
{
  "run_id": "R20260125_143000"
}
```

**2. Identify Low Coverage Areas**
```python
summary = client.coverage.summary(run_id="...")
low_coverage = [
    (scope, data.percentage)
    for scope, data in summary.by_scope.items()
    if data.percentage < 80.0
]
```

**3. Deep Dive into Specific Scope**
```json
{
  "run_id": "R20260125_143000",
  "kind": "functional",
  "scope": "axi_protocol_test"
}
```

### Time-Based Failure Analysis

**Find Failures in Time Window**
```json
{
  "run_id": "R20260125_143000",
  "min_time_ns": 10000,
  "max_time_ns": 20000,
  "sort_by": "time_ns",
  "sort_order": "asc"
}
```

**Analyze Temporal Patterns**
```python
failures = client.failures.list(run_id="...", sort_by="time_ns")
time_clusters = []
current_cluster = []
for f in failures.items:
    if not current_cluster or f.time_ns - current_cluster[-1].time_ns < 1000:
        current_cluster.append(f)
    else:
        time_clusters.append(current_cluster)
        current_cluster = [f]
```

## Filtering Strategies

### By Category

**Protocol Violations**
```json
{"category": "protocol", "severity": "error"}
```

**Functional Issues**
```json
{"category": "functional", "severity": "error"}
```

**Timing Problems**
```json
{"category": "timing", "severity": "warning"}
```

### By Severity

**Critical Issues**
```json
{"severity": "fatal"}
```

**Errors Only**
```json
{"severity": "error"}
```

**All Issues**
```json
{} // No severity filter
```

### By Test

**Specific Test Failures**
```json
{"test_id": "T20260125_143000_axi_burst_test"}
```

**Multiple Tests**
```python
test_ids = ["T1", "T2", "T3"]
all_failures = []
for test_id in test_ids:
    result = client.failures.list(test_id=test_id)
    all_failures.extend(result.items)
```

## Performance Tips

1. **Use Specific Filters**
   ```json
   // ✅ Good - narrow scope
   {
     "run_id": "R20260125_143000",
     "category": "protocol",
     "severity": "error"
   }
   
   // ❌ Bad - too broad
   {
     "severity": "error"
   }
   ```

2. **Paginate Large Result Sets**
   ```json
   {
     "run_id": "R20260125_143000",
     "page": 1,
     "page_size": 50
   }
   ```

3. **Cache Coverage Summaries**
   ```python
   # ✅ Good - single query
   summary = client.coverage.summary(run_id="...")
   functional_pct = summary.by_kind["functional"].percentage
   code_pct = summary.by_kind["code"].percentage
   
   # ❌ Bad - multiple queries
   functional = client.coverage.summary(run_id="...", kind="functional")
   code = client.coverage.summary(run_id="...", kind="code")
   ```

## Visualization Examples

### Failure Heatmap

```python
failures = client.failures.list(run_id="...")
heatmap = {}
for f in failures.items:
    time_bucket = f.time_ns // 10000
    heatmap[time_bucket] = heatmap.get(time_bucket, 0) + 1
```

### Coverage Treemap

```python
summary = client.coverage.summary(run_id="...")
treemap_data = [
    {
        "name": scope,
        "value": data.bins_covered,
        "total": data.bins_total,
        "percentage": data.percentage
    }
    for scope, data in summary.by_scope.items()
]
```

### Assertion Pareto Chart

```python
assertions = client.assertions.list()
failure_counts = []
for a in assertions.items:
    stats = client.assertions.failures(name=a.name, scope=a.scope)
    failure_counts.append((a.name, stats.total_firings))

failure_counts.sort(key=lambda x: x[1], reverse=True)
# Top 20% of assertions cause 80% of failures (Pareto principle)
```

## Next Steps

- [Regression Tools →](regression.md) - Compare runs and track trends
- [Detail Tools →](detail.md) - Investigate specific failures
- [Discovery Tools →](discovery.md) - Find related tests and assertions
