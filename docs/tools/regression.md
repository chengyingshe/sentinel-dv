# Regression Tools

Compare verification runs and track quality trends over time.

## regressions.summary

Get regression analysis between two runs.

### Purpose
Compare test results, identify new failures, fixed issues, and flaky tests.

### Input Schema

```python
class RegressionsSummaryInput(BaseModel):
    baseline_run_id: str
    current_run_id: str
```

### Output Schema

```python
class RegressionsSummaryOutput(BaseModel):
    schema_version: str = "1.0.0"
    item: RegressionSummary

class RegressionSummary(BaseModel):
    baseline_run_id: str
    current_run_id: str
    total_tests: int
    new_passes: int
    new_failures: int
    still_passing: int
    still_failing: int
    flaky_tests: list[str]
    new_failure_details: list[TestComparison]
    fixed_test_details: list[TestComparison]

class TestComparison(BaseModel):
    test_id: str
    test_name: str
    baseline_status: str
    current_status: str
    baseline_duration_ms: int | None
    current_duration_ms: int | None
    failure_diff: FailureDiff | None

class FailureDiff(BaseModel):
    new_assertions: list[str]
    fixed_assertions: list[str]
    changed_messages: dict[str, tuple[str, str]]
```

### Example

**Query**:
```json
{
  "baseline_run_id": "R20260124_143000",
  "current_run_id": "R20260125_143000"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "item": {
    "baseline_run_id": "R20260124_143000",
    "current_run_id": "R20260125_143000",
    "total_tests": 150,
    "new_passes": 5,
    "new_failures": 3,
    "still_passing": 135,
    "still_failing": 7,
    "flaky_tests": [
      "T20260125_143000_axi_timeout_test"
    ],
    "new_failure_details": [
      {
        "test_id": "T20260125_143000_axi_burst_test",
        "test_name": "axi_burst_test",
        "baseline_status": "pass",
        "current_status": "fail",
        "baseline_duration_ms": 14200,
        "current_duration_ms": 15420,
        "failure_diff": {
          "new_assertions": [
            "axi_master_if.axi_awvalid_awready_check",
            "axi_master_if.axi_wvalid_wready_check"
          ],
          "fixed_assertions": [],
          "changed_messages": {}
        }
      },
      {
        "test_id": "T20260125_143000_axi_protocol_test",
        "test_name": "axi_protocol_test",
        "baseline_status": "pass",
        "current_status": "fail",
        "baseline_duration_ms": 11800,
        "current_duration_ms": 12100,
        "failure_diff": {
          "new_assertions": [
            "axi_slave_if.axi_rvalid_rready_check"
          ],
          "fixed_assertions": [],
          "changed_messages": {}
        }
      }
    ],
    "fixed_test_details": [
      {
        "test_id": "T20260125_143000_axi_stress_test",
        "test_name": "axi_stress_test",
        "baseline_status": "fail",
        "current_status": "pass",
        "baseline_duration_ms": 18500,
        "current_duration_ms": 17200,
        "failure_diff": {
          "new_assertions": [],
          "fixed_assertions": [
            "axi_master_if.axi_bvalid_bready_check"
          ],
          "changed_messages": {}
        }
      }
    ]
  }
}
```

---

## runs.diff

Get detailed differences between two runs.

### Purpose
Compare metrics, coverage, and failure patterns across runs.

### Input Schema

```python
class RunsDiffInput(BaseModel):
    baseline_run_id: str
    current_run_id: str
```

### Output Schema

```python
class RunsDiffOutput(BaseModel):
    schema_version: str = "1.0.0"
    item: RunDiff

class RunDiff(BaseModel):
    baseline: RunSummary
    current: RunSummary
    test_status_changes: dict[str, StatusChange]
    coverage_diff: CoverageDiff
    failure_diff: FailureCountDiff

class StatusChange(BaseModel):
    from_status: str
    to_status: str
    count: int

class CoverageDiff(BaseModel):
    functional_delta: float
    code_delta: float
    assertion_delta: float

class FailureCountDiff(BaseModel):
    by_category: dict[str, int]
    by_severity: dict[str, int]
    by_assertion: dict[str, int]
```

### Example

**Query**:
```json
{
  "baseline_run_id": "R20260124_143000",
  "current_run_id": "R20260125_143000"
}
```

**Response**:
```json
{
  "schema_version": "1.0.0",
  "item": {
    "baseline": {
      "run_id": "R20260124_143000",
      "suite": "nightly",
      "status": "pass",
      "total_tests": 150,
      "passed_tests": 143,
      "failed_tests": 7,
      "created_at": "2026-01-24T14:30:00Z",
      "ci_system": "github",
      "ci_build_id": "12344"
    },
    "current": {
      "run_id": "R20260125_143000",
      "suite": "nightly",
      "status": "fail",
      "total_tests": 150,
      "passed_tests": 140,
      "failed_tests": 10,
      "created_at": "2026-01-25T14:30:00Z",
      "ci_system": "github",
      "ci_build_id": "12345"
    },
    "test_status_changes": {
      "pass_to_fail": {
        "from_status": "pass",
        "to_status": "fail",
        "count": 3
      },
      "fail_to_pass": {
        "from_status": "fail",
        "to_status": "pass",
        "count": 5
      }
    },
    "coverage_diff": {
      "functional_delta": -2.5,
      "code_delta": 0.3,
      "assertion_delta": -1.2
    },
    "failure_diff": {
      "by_category": {
        "protocol": 3,
        "functional": -2,
        "timing": 0
      },
      "by_severity": {
        "error": 3,
        "warning": -1
      },
      "by_assertion": {
        "axi_awvalid_awready_check": 5,
        "axi_wvalid_wready_check": 3,
        "axi_bvalid_bready_check": -4
      }
    }
  }
}
```

---

## Common Patterns

### Regression Analysis Workflow

**1. Get High-Level Summary**
```json
{
  "baseline_run_id": "R20260124_143000",
  "current_run_id": "R20260125_143000"
}
```

**2. Identify New Failures**
```python
summary = client.regressions.summary(
    baseline_run_id="R20260124_143000",
    current_run_id="R20260125_143000"
)

if summary.new_failures > 0:
    print(f"⚠️  {summary.new_failures} new test failures!")
    for failure in summary.new_failure_details:
        print(f"  - {failure.test_name}")
        for assertion in failure.failure_diff.new_assertions:
            print(f"    • {assertion}")
```

**3. Investigate Detailed Differences**
```python
diff = client.runs.diff(
    baseline_run_id="R20260124_143000",
    current_run_id="R20260125_143000"
)

# Check coverage regression
if diff.coverage_diff.functional_delta < 0:
    print(f"⚠️  Functional coverage decreased by {abs(diff.coverage_diff.functional_delta):.1f}%")

# Check new failure assertions
for assertion, delta in diff.failure_diff.by_assertion.items():
    if delta > 0:
        print(f"⚠️  '{assertion}' fired {delta} more times")
```

### Trend Analysis

**Compare Multiple Runs**
```python
run_ids = ["R20260121_143000", "R20260122_143000", "R20260123_143000", "R20260124_143000"]

trend = []
for i in range(1, len(run_ids)):
    summary = client.regressions.summary(
        baseline_run_id=run_ids[i-1],
        current_run_id=run_ids[i]
    )
    trend.append({
        "date": run_ids[i],
        "new_failures": summary.new_failures,
        "new_passes": summary.new_passes
    })
```

**Visualize Trend**
```python
import matplotlib.pyplot as plt

dates = [t["date"] for t in trend]
failures = [t["new_failures"] for t in trend]
passes = [t["new_passes"] for t in trend]

plt.plot(dates, failures, label="New Failures", color="red")
plt.plot(dates, passes, label="New Passes", color="green")
plt.legend()
plt.show()
```

### Flaky Test Detection

**Identify Flaky Tests**
```python
summary = client.regressions.summary(
    baseline_run_id="R20260124_143000",
    current_run_id="R20260125_143000"
)

if summary.flaky_tests:
    print(f"⚠️  {len(summary.flaky_tests)} flaky tests detected:")
    for test_id in summary.flaky_tests:
        print(f"  - {test_id}")
```

**Track Flakiness Over Time**
```python
run_ids = ["R1", "R2", "R3", "R4", "R5"]
flaky_history = {}

for i in range(1, len(run_ids)):
    summary = client.regressions.summary(
        baseline_run_id=run_ids[i-1],
        current_run_id=run_ids[i]
    )
    for test_id in summary.flaky_tests:
        flaky_history[test_id] = flaky_history.get(test_id, 0) + 1

# Tests that flaked multiple times
chronic_flaky = {k: v for k, v in flaky_history.items() if v >= 2}
```

### Coverage Tracking

**Monitor Coverage Trends**
```python
run_ids = ["R1", "R2", "R3", "R4"]
coverage_trend = []

for i in range(1, len(run_ids)):
    diff = client.runs.diff(
        baseline_run_id=run_ids[i-1],
        current_run_id=run_ids[i]
    )
    coverage_trend.append({
        "run": run_ids[i],
        "functional": diff.coverage_diff.functional_delta,
        "code": diff.coverage_diff.code_delta,
        "assertion": diff.coverage_diff.assertion_delta
    })
```

**Alert on Coverage Regression**
```python
THRESHOLD = -1.0  # Alert if coverage drops by more than 1%

for entry in coverage_trend:
    if entry["functional"] < THRESHOLD:
        print(f"⚠️  {entry['run']}: Functional coverage dropped {abs(entry['functional']):.1f}%")
```

## Interpretation Guide

### Status Changes

**Positive Changes**
- `fail_to_pass`: Tests that were fixed
- `error_to_pass`: Critical issues resolved
- `skipped_to_pass`: Tests re-enabled and passing

**Negative Changes**
- `pass_to_fail`: New regressions (investigate immediately)
- `pass_to_error`: Critical new issues (highest priority)
- `fail_to_error`: Worsening failures

**Neutral Changes**
- `still_passing`: Stable tests (good)
- `still_failing`: Known issues (track separately)

### Coverage Deltas

**Interpretation**:
- `> 0`: Coverage improved ✅
- `0`: No change (acceptable)
- `< 0`: Coverage decreased ⚠️ (investigate)

**Thresholds**:
- `< -5%`: Critical regression
- `-5% to -1%`: Warning
- `-1% to 0%`: Minor decrease
- `0% to 1%`: Stable
- `> 1%`: Improvement

### Failure Count Deltas

**By Category**:
- `protocol > 0`: New protocol violations (high priority)
- `functional > 0`: New functional issues
- `timing > 0`: New timing problems

**By Severity**:
- `fatal > 0`: New critical issues (block release)
- `error > 0`: New errors (investigate)
- `warning > 0`: New warnings (monitor)

## Best Practices

1. **Baseline Selection**
   ```python
   # ✅ Good - compare with last passing run
   last_pass = next(
       r for r in runs
       if r.status == "pass"
   )
   summary = client.regressions.summary(
       baseline_run_id=last_pass.run_id,
       current_run_id=current_run_id
   )
   
   # ❌ Bad - compare with arbitrary run
   summary = client.regressions.summary(
       baseline_run_id="R_old",
       current_run_id=current_run_id
   )
   ```

2. **Flaky Test Handling**
   ```python
   # ✅ Good - track flakiness over multiple runs
   flaky_threshold = 2
   if flaky_history.get(test_id, 0) >= flaky_threshold:
       mark_test_as_flaky(test_id)
   
   # ❌ Bad - single-run flakiness detection
   if test_id in summary.flaky_tests:
       mark_test_as_flaky(test_id)
   ```

3. **Coverage Regression**
   ```python
   # ✅ Good - consider multiple coverage kinds
   if any([
       diff.coverage_diff.functional_delta < -1.0,
       diff.coverage_diff.code_delta < -2.0,
       diff.coverage_diff.assertion_delta < -1.0
   ]):
       alert_coverage_regression()
   
   # ❌ Bad - only check one kind
   if diff.coverage_diff.functional_delta < 0:
       alert_coverage_regression()
   ```

## Integration Examples

### CI/CD Pipeline

```python
def check_regression(baseline_run_id: str, current_run_id: str) -> bool:
    """Return True if regression detected."""
    summary = client.regressions.summary(
        baseline_run_id=baseline_run_id,
        current_run_id=current_run_id
    )
    
    # Fail if new failures
    if summary.new_failures > 0:
        print(f"❌ {summary.new_failures} new test failures")
        return True
    
    # Fail if coverage regressed
    diff = client.runs.diff(
        baseline_run_id=baseline_run_id,
        current_run_id=current_run_id
    )
    if diff.coverage_diff.functional_delta < -1.0:
        print(f"❌ Functional coverage decreased by {abs(diff.coverage_diff.functional_delta):.1f}%")
        return True
    
    print("✅ No regressions detected")
    return False
```

### GitHub PR Comment

```python
def generate_pr_comment(summary: RegressionSummary) -> str:
    """Generate markdown comment for PR."""
    lines = [
        "## Regression Analysis",
        "",
        f"**Baseline**: `{summary.baseline_run_id}`",
        f"**Current**: `{summary.current_run_id}`",
        "",
        "### Summary",
        f"- ✅ New passes: {summary.new_passes}",
        f"- ❌ New failures: {summary.new_failures}",
        f"- ⚠️  Flaky tests: {len(summary.flaky_tests)}",
        ""
    ]
    
    if summary.new_failures > 0:
        lines.extend([
            "### New Failures",
            ""
        ])
        for failure in summary.new_failure_details:
            lines.append(f"- `{failure.test_name}`")
            for assertion in failure.failure_diff.new_assertions:
                lines.append(f"  - {assertion}")
    
    return "\n".join(lines)
```

## Next Steps

- [Analysis Tools →](analysis.md) - Investigate failure patterns
- [Detail Tools →](detail.md) - Inspect specific test changes
- [Discovery Tools →](discovery.md) - Find related runs and tests
