# ID Strategy

## Goals

- **Stability**: IDs must remain stable across machines, paths, and indexing time
- **Determinism**: Same artifacts + same config ⇒ identical IDs
- **Collision resistance**: Use cryptographic hashing
- **Privacy**: Avoid embedding sensitive raw strings; hash normalized representations instead
- **Traceability**: IDs must be reproducible from stored index fields

## Canonical Hashing

### Hash Algorithm

- **Primary**: SHA-256
- **ID encoding**: lowercase hex
- **ID format**: `<prefix>_<hex12>` for compact IDs exposed via MCP; store full sha256 internally
- **Example**: `t_ab12cd34ef56`

**Rationale**: Clients get short IDs; store retains full hash for collision detection and audit.

### Canonical Serialization

All hash inputs must use a canonical serialization:

- JSON with:
  - sorted keys
  - UTF-8 encoding
  - no whitespace
- Normalize strings (see below) before serialization

### String Normalization

Applies to all ID inputs:

- Trim leading/trailing whitespace
- Normalize line endings to `\n`
- Lowercase where the semantic field is case-insensitive (e.g., framework name, simulator vendor)
- Replace platform-dependent path separators (`\` → `/`)
- Remove volatile substrings (see "Volatile stripping")

### Volatile Stripping (for stability)

Remove/normalize values known to vary between runs but not semantically part of identity:

- Absolute filesystem prefixes (replace with `<ROOT>` before hashing)
- Hostnames (replace with `<HOST>`)
- Timestamps (replace with `<TS>`)
- Random temporary directory names (replace with `<TMP>`)

This is applied only where those values might leak into identity fields (typically evidence paths and raw messages).

---

## run_id Strategy

### Preferred (CI-backed) run_id

If CI metadata exists:

```python
run_id_full = sha256(canonical_json({
    "suite": <suite>,
    "ci_system": <ci.system>,
    "ci_build_id": <ci.build_id>,
    "ci_job_url": <normalized_url(ci.job_url)>
}))
```

### Fallback (artifact-backed) run_id

If CI metadata is absent:

```python
# Use stable fingerprint of the artifact set
artifact_manifest_hash = sha256(concat(sorted([
    relative_path + ":" + file_sha256
])))

run_id_full = sha256(canonical_json({
    "suite": <suite>,
    "artifact_manifest": <artifact_manifest_hash>
}))
```

### Exposed run_id

```python
run_id = "r_" + hex12(run_id_full)
```

---

## test_id Strategy

### Inputs

A `test_id` should uniquely identify a test instance within a run.

Hash input:

```json
{
  "run_id_full": "<full sha256 of run_id>",
  "framework": "uvm|cocotb|sv_unit|unknown",
  "test_name": "<normalized test name>",
  "seed": <int|null>,
  "simulator_vendor": "<normalized vendor|null>",
  "simulator_version": "<normalized version|null>",
  "dut_top": "<normalized top|null>"
}
```

**Notes**:
- `seed` is included when present because it materially changes behavior in DV
- If your environment has an explicit test GUID (some harnesses do), include that as `test_guid` and optionally omit other fields

### Computation

```python
test_id_full = sha256(canonical_json(inputs))
test_id = "t_" + hex12(test_id_full)
```

---

## failure_id Strategy

### What a Failure Event Is

A `FailureEvent` is a normalized record of something that went wrong, typically derived from:

- UVM report lines
- cocotb exception traces
- assertion failure entries
- compile/elab errors

### Inputs

Failures must be uniquely addressable within a test, but stable across indexing.

Hash input:

```json
{
  "test_id_full": "<full sha256 of test_id>",
  "severity": "info|warning|error|fatal",
  "category": "...",
  "summary_norm": "<normalized summary>",
  "component_norm": "<normalized component|null>",
  "phase_norm": "<normalized phase|null>",
  "time_bucket": "<time bucket|null>",
  "evidence_fingerprint": "<optional>"
}
```

### time_bucket

To prevent instability from minor timestamp differences, use bucketing:

- If time is available: `time_bucket = floor(time_ns / 1000)` (1 µs buckets)
- If only log line exists without time: `null`

### evidence_fingerprint

Optional but useful when multiple identical summaries exist:

```python
evidence_fingerprint = sha256(concat(sorted([
    path + ":" + start_line + ":" + end_line
])))
```

Only include if evidence exists; otherwise omit.

### Computation

```python
failure_id_full = sha256(canonical_json(inputs))
failure_id = "f_" + hex12(failure_id_full)
```

---

## signature_id Strategy (Regression Clustering)

### Purpose

A `FailureSignature` clusters failures across tests/runs.

### Inputs

Signature should represent the **type** of failure, not the instance.

Hash input:

```json
{
  "category": "...",
  "summary_signature": "<signature-normalized summary>",
  "protocol": "<protocol tag|null>",
  "component_role": "<optional normalized role|null>"
}
```

### signature-normalized summary

Apply stronger normalization than `summary_norm`:

- Replace hex literals: `0x[0-9a-fA-F]+` → `<HEX>`
- Replace decimal numbers: `\b\d+\b` → `<NUM>`
- Replace time units: `123ns`, `45 us` → `<TIME>`
- Replace paths: `/.../file.sv` → `<PATH>`
- Replace instance paths: `tb.top.env.agent[3].drv` → `<INST>` (optional, configurable)
- Collapse whitespace

### Computation

```python
signature_id_full = sha256(canonical_json(inputs))
signature_id = "s_" + hex12(signature_id_full)
```

---

## Collision Handling

- Store full hashes (`*_id_full`) in the index
- If two different records yield same short ID (hex12 collision), server must:
  - still disambiguate internally by full hash
  - expose a longer prefix (configurable) for those IDs or include full hash in details responses
- In practice, SHA-256 with 12 hex chars (48 bits) is typically sufficient, but collision handling must exist

---

## Implementation Reference

See `sentinel_dv/ids.py` for the canonical implementation.
