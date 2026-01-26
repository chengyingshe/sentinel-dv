# Performance Optimization

Optimize Sentinel DV for fast indexing and responsive queries.

## Indexing Performance

### Parallel Processing

**Enable Workers**:
```bash
sentinel-dv index \
  --workers 8 \
  --log-dir ./results \
  --output ./sentinel_db
```

**Optimal Worker Count**:
- CPU cores: Use `nproc` or `sysctl -n hw.ncpu`
- Recommended: `min(cpu_cores - 1, 8)`
- Memory-bound: Reduce workers if OOM errors occur

**Python API**:
```python
from sentinel_dv import SentinelDV

client = SentinelDV(
    db_path="./sentinel_db",
    workers=8  # Parallel indexing
)

client.index_run(
    run_id="R20260125_143000",
    log_dir="./results/run1"
)
```

---

### Incremental Indexing

**Only Index New Runs**:
```bash
# First run - full index
sentinel-dv index --log-dir ./results --output ./sentinel_db

# Subsequent runs - incremental
sentinel-dv index \
  --log-dir ./results/new_run \
  --run-id R20260125_150000 \
  --output ./sentinel_db \
  --incremental
```

**Python API**:
```python
# Check if run already indexed
if not client.runs.exists(run_id="R20260125_143000"):
    client.index_run(run_id="R20260125_143000", log_dir="...")
```

---

### Selective Indexing

**Index Only Required Artifacts**:
```bash
sentinel-dv index \
  --log-dir ./results \
  --skip-waveforms \
  --skip-coverage \
  --output ./sentinel_db
```

**Options**:
- `--skip-waveforms`: Skip waveform summary extraction (fastest)
- `--skip-coverage`: Skip coverage parsing
- `--skip-assertions`: Skip assertion extraction
- `--logs-only`: Only parse test logs

**Use Case**: CI/CD where only test results needed

---

### Batch Processing

**Index Multiple Runs**:
```bash
# index_all.sh
for run_dir in ./results/R*; do
  sentinel-dv index \
    --log-dir "$run_dir" \
    --run-id $(basename "$run_dir") \
    --output ./sentinel_db \
    --incremental
done
```

**Parallel Batch**:
```bash
# index_parallel.sh
find ./results -name "R*" -type d | \
  parallel -j 4 sentinel-dv index \
    --log-dir {} \
    --run-id {/} \
    --output ./sentinel_db \
    --incremental
```

---

## Query Performance

### Pagination

**Use Appropriate Page Sizes**:
```python
# ✅ Good - reasonable page size
tests = client.tests.list(
    run_id="R20260125_143000",
    page=1,
    page_size=50  # 50-100 optimal
)

# ❌ Bad - too large
tests = client.tests.list(
    run_id="R20260125_143000",
    page=1,
    page_size=1000  # Slow, high memory
)
```

**Paginate Large Results**:
```python
def fetch_all_tests(run_id: str):
    page = 1
    while True:
        result = client.tests.list(
            run_id=run_id,
            page=page,
            page_size=100
        )
        yield from result.items
        
        if page >= result.total_pages:
            break
        page += 1
```

---

### Filtering

**Use Specific Filters**:
```python
# ✅ Good - narrow scope
tests = client.tests.list(
    run_id="R20260125_143000",  # Specific run
    framework="uvm",             # Specific framework
    status="fail"                # Specific status
)

# ❌ Bad - too broad
tests = client.tests.list()  # All tests, all runs
```

**Filter Early**:
```python
# ✅ Good - filter in query
failed_tests = client.tests.list(
    run_id="R20260125_143000",
    status="fail"
)

# ❌ Bad - filter after fetching
all_tests = client.tests.list(run_id="R20260125_143000")
failed_tests = [t for t in all_tests.items if t.status == "fail"]
```

---

### Caching

**Cache Frequently Accessed Data**:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_test_cached(test_id: str):
    return client.tests.get(test_id=test_id)

# Subsequent calls use cache
test1 = get_test_cached("T20260125_143000_axi_burst_test")  # API call
test2 = get_test_cached("T20260125_143000_axi_burst_test")  # Cached
```

**Cache Run Summaries**:
```python
# Cache run summaries for 5 minutes
import time

run_cache = {}
CACHE_TTL = 300  # 5 minutes

def get_run_summary(run_id: str):
    now = time.time()
    if run_id in run_cache:
        cached_data, timestamp = run_cache[run_id]
        if now - timestamp < CACHE_TTL:
            return cached_data
    
    data = client.runs.get(run_id=run_id)
    run_cache[run_id] = (data, now)
    return data
```

---

### Batch Queries

**Fetch Related Data in Parallel**:
```python
import asyncio

async def fetch_test_details(test_ids: list[str]):
    tasks = [
        asyncio.to_thread(client.tests.get, test_id=tid)
        for tid in test_ids
    ]
    return await asyncio.gather(*tasks)

# Usage
test_ids = ["T1", "T2", "T3", "T4", "T5"]
tests = asyncio.run(fetch_test_details(test_ids))
```

---

## Database Optimization

### Indexing Strategy

**Create Indexes**:
```python
# Internal SQLite indexes
# Automatically created on:
# - run_id
# - test_id
# - status
# - framework
# - assertion_name + assertion_scope
```

**Custom Indexes** (advanced):
```python
# If using direct SQLite access
import sqlite3

conn = sqlite3.connect("./sentinel_db/index.db")
cursor = conn.cursor()

# Index for frequent queries
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_tests_created_at
    ON tests(created_at)
""")
conn.commit()
```

---

### Database Cleanup

**Remove Old Runs**:
```bash
sentinel-dv cleanup \
  --older-than 30d \
  --output ./sentinel_db
```

**Python API**:
```python
from datetime import datetime, timedelta

# Delete runs older than 30 days
cutoff = datetime.now() - timedelta(days=30)
client.cleanup(older_than=cutoff)
```

---

### Vacuum Database

**Reclaim Space**:
```bash
sentinel-dv vacuum --output ./sentinel_db
```

**Automatic Vacuum**:
```python
# config.yaml
database:
  auto_vacuum: true
  vacuum_interval: 7d  # Vacuum weekly
```

---

## Memory Management

### Streaming Large Results

**Use Generators**:
```python
def stream_failures(run_id: str):
    """Stream failures without loading all into memory."""
    page = 1
    while True:
        result = client.failures.list(
            run_id=run_id,
            page=page,
            page_size=100
        )
        
        for failure in result.items:
            yield failure
        
        if page >= result.total_pages:
            break
        page += 1

# Process one at a time
for failure in stream_failures("R20260125_143000"):
    process_failure(failure)
```

---

### Limit Context Size

**Avoid Large Nested Objects**:
```python
# ✅ Good - fetch only required fields
test_summary = client.tests.list(run_id="...")  # Only summary fields

# ❌ Bad - fetch full details for all tests
all_tests = [
    client.tests.get(test_id=t.test_id)
    for t in client.tests.list(run_id="...").items
]
```

---

### Garbage Collection

**Explicit GC for Long-Running Processes**:
```python
import gc

# Process many runs
for run_id in large_run_list:
    client.index_run(run_id=run_id, log_dir=f"./results/{run_id}")
    
    # Force garbage collection
    gc.collect()
```

---

## Network Optimization

### Connection Pooling

**Reuse Client Instances**:
```python
# ✅ Good - single client instance
client = SentinelDV(db_path="./sentinel_db")

for run_id in runs:
    summary = client.runs.get(run_id=run_id)

# ❌ Bad - create new client each time
for run_id in runs:
    client = SentinelDV(db_path="./sentinel_db")
    summary = client.runs.get(run_id=run_id)
```

---

### Compression

**Enable Response Compression**:
```python
client = SentinelDV(
    db_path="./sentinel_db",
    compression=True  # Compress large responses
)
```

---

## Monitoring

### Performance Metrics

**Enable Timing**:
```python
import time

def timed_query(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"{func.__name__}: {elapsed:.2f}s")
    return result

# Usage
tests = timed_query(
    client.tests.list,
    run_id="R20260125_143000",
    status="fail"
)
```

---

### Query Profiling

**Profile Slow Queries**:
```python
import cProfile

def analyze_failures():
    failures = client.failures.list(
        run_id="R20260125_143000",
        category="protocol"
    )
    for f in failures.items:
        process(f)

cProfile.run('analyze_failures()', sort='cumtime')
```

---

## Best Practices

### 1. Index Strategy

**Fast Indexing**:
```bash
# CI/CD: Logs only, skip artifacts
sentinel-dv index \
  --logs-only \
  --workers 4 \
  --log-dir ./results

# Nightly: Full index with artifacts
sentinel-dv index \
  --workers 8 \
  --log-dir ./results \
  --waveforms \
  --coverage
```

---

### 2. Query Patterns

**Efficient Queries**:
```python
# Pattern 1: Filter → Detail
# ✅ Good
failed_tests = client.tests.list(status="fail")
for test_summary in failed_tests.items:
    details = client.tests.get(test_id=test_summary.test_id)

# Pattern 2: Cache → Reuse
# ✅ Good
@lru_cache
def get_run_info(run_id: str):
    return client.runs.get(run_id=run_id)
```

---

### 3. Resource Limits

**Set Limits**:
```python
# config.yaml
performance:
  max_workers: 8
  max_page_size: 100
  max_query_time_ms: 5000
  max_memory_mb: 4096
```

---

### 4. Error Handling

**Graceful Degradation**:
```python
def safe_query(func, *args, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except TimeoutError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## Benchmarks

### Typical Performance

**Indexing**:
- Small run (10 tests): ~1 second
- Medium run (100 tests): ~5 seconds
- Large run (1000 tests): ~30 seconds
- With coverage/waveforms: 2-3x slower

**Queries**:
- List tests (page=1, size=50): ~10-50ms
- Get test detail: ~5-20ms
- Failure analysis: ~50-200ms
- Regression summary: ~100-500ms

---

### Optimization Impact

| Optimization | Speedup | Memory Saved |
|--------------|---------|--------------|
| Parallel indexing (8 workers) | 6-7x | - |
| Skip waveforms | 2-3x | - |
| Pagination (50 vs 1000) | - | 10-20x |
| Caching (hot queries) | 50-100x | - |
| Incremental indexing | 10-100x | - |

---

## Troubleshooting

### Slow Indexing

**Problem**: Indexing takes too long

**Solutions**:
1. Enable parallel workers: `--workers 8`
2. Skip artifacts: `--logs-only`
3. Use incremental: `--incremental`
4. Check disk I/O: `iostat -x 1`

---

### High Memory Usage

**Problem**: OOM errors during indexing

**Solutions**:
1. Reduce workers: `--workers 2`
2. Process runs individually
3. Enable streaming: `--stream`
4. Increase swap space

---

### Slow Queries

**Problem**: Queries take seconds to return

**Solutions**:
1. Add filters: `run_id`, `status`, etc.
2. Reduce page size: `page_size=50`
3. Enable caching
4. Vacuum database: `sentinel-dv vacuum`

---

## Next Steps

- [Simulator Support →](simulator-support.md) - Optimize for specific simulators
- [Custom Adapters →](../adapters/custom.md) - Implement efficient parsers
- [Architecture →](../architecture/overview.md) - Understand internal design
