# Security Model

Sentinel DV implements defense-in-depth security for AI agent access to verification artifacts.

## Security Principles

### 1. Read-Only by Design

**No Simulator Control**
- Cannot run simulations
- Cannot execute commands
- Cannot modify artifacts
- Cannot access system resources

**Query-Only Interface**
- All tools are read-only queries
- No write operations exposed
- No configuration changes via MCP
- Immutable indexed data

### 2. Automatic Redaction

All outputs are automatically scanned and sensitive data is redacted:

**Credentials**
```
AWS Keys:     AKIAIOSFODNN7EXAMPLE → [REDACTED]
GitHub PATs:  ghp_abc123... → [REDACTED]
OpenAI Keys:  sk-proj-abc... → [REDACTED]
GitLab Tokens: glpat-xxx... → [REDACTED]
Bearer Tokens: Bearer abc... → [REDACTED]
SSH Keys:     ssh-rsa AAA... → [REDACTED]
```

**File Paths**
```
Absolute:  /home/user/project/sim.log → [REDACTED]
Home dir:  ~/workspace/test.log → [REDACTED]
Relative:  results/test.log → results/test.log ✓
```

**Configurable Redaction**
```yaml
# config.yaml
security:
  redaction:
    redact_emails: false  # Optional: redact email addresses
    redact_paths: true    # Recommended: redact absolute paths
    custom_patterns:
      - pattern: "INTERNAL_TOKEN_\\w+"
        replacement: "[INTERNAL_TOKEN]"
```

### 3. Path Sandboxing

All file path references are validated and constrained:

**Allowed Paths**
- ✅ Relative paths within artifact_roots
- ✅ Filenames without directory traversal
- ✅ Paths validated against allow-list

**Blocked Paths**
- ❌ Absolute paths (e.g., `/etc/passwd`)
- ❌ Parent directory traversal (e.g., `../../secret`)
- ❌ Home directory references (e.g., `~/.ssh/`)
- ❌ Symlinks outside sandbox
- ❌ Device files (e.g., `/dev/null`)

**Implementation**
```python
from sentinel_dv.schemas.common import EvidenceRef

# Valid - relative path
ref = EvidenceRef(kind="log", path="sim_results/test.log")

# Invalid - absolute path
ref = EvidenceRef(kind="log", path="/tmp/test.log")
# Raises: ValidationError: Absolute paths not allowed

# Invalid - traversal
ref = EvidenceRef(kind="log", path="../../../etc/passwd")
# Raises: ValidationError: Path traversal not allowed
```

### 4. Bounded Outputs

All responses have strict size limits to prevent denial-of-service:

| Output Type | Limit | Rationale |
|-------------|-------|-----------|
| Log lines | 1,000 lines | Prevents memory exhaustion |
| Text fields | 50 KB | Keeps LLM context manageable |
| Array items | 1,000 items | Prevents infinite loops |
| Page size | 100 items | Reasonable batch size |
| Evidence extract | 5,000 chars | Sufficient for context |

**Automatic Truncation**
```python
# Long text is automatically truncated
message = "..." * 100000
truncated = truncate_text(message, max_length=2000)
# Returns: first 2000 chars + "... (truncated)"
```

**Pagination**
```json
{
  "page": 1,
  "page_size": 50,  // Max 100
  "total_items": 1500,
  "items": [...]
}
```

### 5. Input Validation

All inputs are strictly validated using Pydantic schemas:

**Type Safety**
```python
# All inputs typed and validated
class TestsListInput(BaseModel):
    run_id: str = Field(..., min_length=1)
    framework: Framework | None = None  # Literal type
    status: TestStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
```

**Enum Constraints**
```python
Framework = Literal["uvm", "cocotb", "sv_unit", "unknown"]
TestStatus = Literal["pass", "fail", "error", "skipped", "unknown"]
Severity = Literal["info", "warning", "error", "fatal"]
```

**Pattern Validation**
```python
# IDs must match specific patterns
run_id: str = Field(..., pattern=r"^R\d{8}_\d{6}$")
test_id: str = Field(..., pattern=r"^T\d{8}_\d{6}_\w+$")
```

## Threat Model

### In Scope

1. **Credential Leakage**
   - Mitigation: Automatic redaction
   - Coverage: Common credential formats
   - Configurable patterns

2. **Path Traversal**
   - Mitigation: Path sandboxing + validation
   - Block: Absolute paths, `..`, symlinks
   - Allow-list enforcement

3. **Resource Exhaustion (DoS)**
   - Mitigation: Bounded outputs + pagination
   - Limits: File sizes, array lengths, text fields
   - Timeouts: Query execution limits

4. **Data Injection**
   - Mitigation: Input validation + type safety
   - No SQL injection (parameterized queries)
   - No command injection (no shell execution)

### Out of Scope

1. **Physical Access**
   - Requires: File system access control
   - Defense: OS-level permissions

2. **Network Security**
   - Requires: HTTPS/TLS for transport
   - Defense: MCP transport layer

3. **Authentication**
   - Handled by: MCP client (Claude Desktop)
   - Not part of: Sentinel DV server

4. **Rate Limiting**
   - Handled by: MCP client
   - Server-side: Query timeouts only

## Configuration

### Minimal Security Setup

```yaml
# config.yaml
artifact_roots:
  - ./regression_results  # Relative path recommended

security:
  # Size limits
  max_log_lines: 1000
  max_text_size_bytes: 51200  # 50 KB
  max_array_items: 1000
  
  # Redaction
  redaction:
    redact_emails: false
    redact_paths: true
    custom_patterns: []

  # Path sandboxing (always enforced)
  allow_absolute_paths: false  # Recommended: false
```

### Production Setup

```yaml
# config.yaml - Production
artifact_roots:
  - /data/verification/nightly
  - /data/verification/release

security:
  # Stricter limits for production
  max_log_lines: 500
  max_text_size_bytes: 25600  # 25 KB
  max_array_items: 500
  
  # Aggressive redaction
  redaction:
    redact_emails: true
    redact_paths: true
    custom_patterns:
      - pattern: "COMPANY_SECRET_\\w+"
        replacement: "[COMPANY_SECRET]"
      - pattern: "api_key=\\w+"
        replacement: "api_key=[REDACTED]"

  # Strict sandboxing
  allow_absolute_paths: false
```

## Audit & Monitoring

### Logging

Sentinel DV logs all MCP tool calls:

```python
# Logged per request
{
  "timestamp": "2026-01-25T14:30:00Z",
  "tool": "tests.get",
  "input": {"test_id": "T20260125_143000_axi_burst"},
  "user": "claude-desktop",
  "duration_ms": 45,
  "status": "success"
}
```

### Metrics

Track security events:

```python
# Redaction metrics
redactions_applied: 123
credential_types_redacted: ["aws_key", "github_token"]
paths_sanitized: 456

# Validation failures
invalid_paths_blocked: 12
traversal_attempts_blocked: 3
oversized_requests_rejected: 2
```

## Best Practices

### For Users

1. **Limit Artifact Roots**
   ```yaml
   # ✅ Good - specific directories
   artifact_roots:
     - ./regression_results
     - ./nightly_results
   
   # ❌ Bad - too broad
   artifact_roots:
     - /
     - ~
   ```

2. **Enable Path Redaction**
   ```yaml
   security:
     redaction:
       redact_paths: true  # ✅ Always on
   ```

3. **Review Logs Periodically**
   ```bash
   # Check for suspicious patterns
   grep "traversal_attempt" sentinel_dv.log
   grep "invalid_path" sentinel_dv.log
   ```

### For Developers

1. **Always Use Schemas**
   ```python
   # ✅ Good - validated
   from sentinel_dv.schemas.tests import TestCase
   test = TestCase(**raw_data)
   
   # ❌ Bad - unvalidated
   test = raw_data
   ```

2. **Apply Bounds**
   ```python
   from sentinel_dv.utils.bounded_text import truncate_text
   
   # ✅ Always truncate potentially large text
   message = truncate_text(log_content, max_length=2000)
   ```

3. **Validate Paths**
   ```python
   from sentinel_dv.schemas.common import EvidenceRef
   
   # Validation happens automatically
   evidence = EvidenceRef(kind="log", path=relative_path)
   ```

## Security Disclosure

Found a security issue? Please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. Email: security@example.com (replace with your contact)
3. Include: Description, reproduction steps, impact assessment
4. We will respond within 48 hours

## FAQ

**Q: Can Sentinel DV run simulations?**  
A: No. It's read-only and only accesses pre-generated artifacts.

**Q: Can I disable redaction?**  
A: You can configure patterns, but path sandboxing is always enforced.

**Q: What if I need absolute paths in evidence?**  
A: Use relative paths from artifact_roots. They're more portable anyway.

**Q: How do I add custom redaction patterns?**  
A: Add them to `security.redaction.custom_patterns` in config.yaml.

**Q: Is Sentinel DV safe for production verification data?**  
A: Yes, with proper configuration. Enable all redactions and use restrictive artifact_roots.
