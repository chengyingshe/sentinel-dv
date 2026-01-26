# Discovery Tools

Find and list verification artifacts with powerful filtering and pagination.

## runs.list

List indexed verification runs.

### Purpose
Search and filter verification runs by suite, status, time range, and CI metadata.

### Input Schema

```python
class RunsListInput(BaseModel):
    suite: str | None = None
    status: Literal["pass", "fail", "error"] | None = None
    ci_system: str | None = None  # "github", "jenkins", "gitlab"
    ci_build_id: str | None = None
    created_after: str | None = None  # RFC3339 timestamp
    created_before: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: Literal["created_at", "total_tests"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
```

### Output Schema

```python
class RunsListOutput(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[RunSummary]

class RunSummary(BaseModel):
    run_id: str
    suite: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    created_at: str
    ci_system: str | None
    ci_build_id: str | None
```

### Example

**Query**:
```json
{
  "suite": "nightly",
  "status": "fail",
  "created_after": "2026-01-20T00:00:00Z",
  "page": 1,
  "page_size": 10
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 10,
  "total_items": 5,
  "total_pages": 1,
  "items": [
    {
      "run_id": "R20260125_143000",
      "suite": "nightly",
      "status": "fail",
      "total_tests": 150,
      "passed_tests": 138,
      "failed_tests": 12,
      "created_at": "2026-01-25T14:30:00Z",
      "ci_system": "github",
      "ci_build_id": "12345"
    }
  ]
}
```

---

## tests.list

List tests from verification runs.

### Purpose
Find tests by framework, status, name pattern, and run ID.

### Input Schema

```python
class TestsListInput(BaseModel):
    run_id: str | None = None
    framework: Framework | None = None  # "uvm" | "cocotb" | "sv_unit"
    status: TestStatus | None = None  # "pass" | "fail" | "error" | "skipped"
    name_contains: str | None = None
    has_failures: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: Literal["name", "duration_ms", "created_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
```

### Output Schema

```python
class TestsListOutput(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[TestSummary]

class TestSummary(BaseModel):
    test_id: str
    name: str
    framework: str
    status: str
    duration_ms: int | None
    failure_count: int
    run_id: str
```

### Example

**Query**:
```json
{
  "run_id": "R20260125_143000",
  "framework": "uvm",
  "status": "fail",
  "name_contains": "axi"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 50,
  "total_items": 3,
  "total_pages": 1,
  "items": [
    {
      "test_id": "T20260125_143000_axi_burst_test",
      "name": "axi_burst_test",
      "framework": "uvm",
      "status": "fail",
      "duration_ms": 15420,
      "failure_count": 3,
      "run_id": "R20260125_143000"
    },
    {
      "test_id": "T20260125_143000_axi_protocol_test",
      "name": "axi_protocol_test",
      "framework": "uvm",
      "status": "fail",
      "duration_ms": 12100,
      "failure_count": 1,
      "run_id": "R20260125_143000"
    }
  ]
}
```

---

## assertions.list

List assertion definitions indexed from HDL sources.

### Purpose
Search assertions by scope, protocol, tags, and severity.

### Input Schema

```python
class AssertionsListInput(BaseModel):
    scope: str | None = None  # Module/interface path
    protocol: Protocol | None = None  # "AXI4" | "PCIe" | ...
    tags: list[str] | None = None
    severity: Severity | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
```

### Output Schema

```python
class AssertionsListOutput(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[AssertionSummary]

class AssertionSummary(BaseModel):
    name: str
    scope: str
    protocol: str | None
    severity: str
    intent: str
    tags: list[str]
```

### Example

**Query**:
```json
{
  "protocol": "AXI4",
  "severity": "error",
  "tags": ["handshake"]
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 50,
  "total_items": 2,
  "total_pages": 1,
  "items": [
    {
      "name": "axi_awvalid_awready_check",
      "scope": "axi_master_if",
      "protocol": "AXI4",
      "severity": "error",
      "intent": "AWVALID must remain high until AWREADY asserted",
      "tags": ["handshake", "axi4", "write-channel"]
    },
    {
      "name": "axi_wvalid_wready_check",
      "scope": "axi_master_if",
      "protocol": "AXI4",
      "severity": "error",
      "intent": "WVALID must remain high until WREADY asserted",
      "tags": ["handshake", "axi4", "write-data"]
    }
  ]
}
```

---

## coverage.list

List coverage summaries from runs.

### Purpose
Find coverage data by run, kind (functional/code/assertion), and scope.

### Input Schema

```python
class CoverageListInput(BaseModel):
    run_id: str | None = None
    kind: CoverageKind | None = None  # "functional" | "code" | "assertion"
    scope: str | None = None
    min_percentage: float | None = Field(None, ge=0, le=100)
    max_percentage: float | None = Field(None, ge=0, le=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
```

### Output Schema

```python
class CoverageListOutput(BaseModel):
    schema_version: str = "1.0.0"
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[CoverageSummaryBrief]

class CoverageSummaryBrief(BaseModel):
    run_id: str
    kind: str
    scope: str
    overall_percentage: float
    bins_total: int
    bins_covered: int
```

### Example

**Query**:
```json
{
  "run_id": "R20260125_143000",
  "kind": "functional",
  "max_percentage": 90.0
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "page": 1,
  "page_size": 50,
  "total_items": 2,
  "total_pages": 1,
  "items": [
    {
      "run_id": "R20260125_143000",
      "kind": "functional",
      "scope": "axi_burst_test",
      "overall_percentage": 87.5,
      "bins_total": 120,
      "bins_covered": 105
    },
    {
      "run_id": "R20260125_143000",
      "kind": "functional",
      "scope": "axi_protocol_test",
      "overall_percentage": 82.3,
      "bins_total": 96,
      "bins_covered": 79
    }
  ]
}
```

---

## Common Patterns

### Pagination

All list tools support consistent pagination:

```json
{
  "page": 1,
  "page_size": 50,
  "sort_by": "created_at",
  "sort_order": "desc"
}
```

Responses include pagination metadata:

```json
{
  "page": 1,
  "page_size": 50,
  "total_items": 150,
  "total_pages": 3,
  "items": [...]
}
```

### Filtering

Most tools support multiple filters with AND semantics:

```json
{
  "status": "fail",
  "framework": "uvm",
  "name_contains": "axi"
}
```

This returns only tests that match ALL conditions.

### Sorting

Customize result ordering:

```json
{
  "sort_by": "duration_ms",
  "sort_order": "desc"
}
```

Common sort fields:
- `created_at`: Timestamp (default)
- `name`: Alphabetical
- `duration_ms`: Execution time
- `percentage`: Coverage metrics

### Time Ranges

Use RFC3339 timestamps for time filtering:

```json
{
  "created_after": "2026-01-20T00:00:00Z",
  "created_before": "2026-01-26T00:00:00Z"
}
```

## Performance Tips

1. **Use Specific Filters**
   ```json
   // ✅ Good - narrow scope
   {"run_id": "R20260125_143000", "status": "fail"}
   
   // ❌ Bad - too broad
   {"page_size": 100}
   ```

2. **Paginate Large Results**
   ```json
   // ✅ Good - reasonable page size
   {"page": 1, "page_size": 50}
   
   // ❌ Bad - too large
   {"page": 1, "page_size": 100}
   ```

3. **Limit Returned Fields**
   ```json
   // Future: field selection
   {"fields": ["test_id", "name", "status"]}
   ```

## Next Steps

- [Detail Tools →](detail.md) - Get comprehensive item details
- [Analysis Tools →](analysis.md) - Analyze failures and coverage
- [Regression Tools →](regression.md) - Compare runs and track trends
