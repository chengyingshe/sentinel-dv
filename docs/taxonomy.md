# Taxonomy Rules

## Objectives

- Normalize noisy verification outputs into consistent:
  - `severity`
  - `category`
  - `tags[]`
- Provide deterministic, explainable mapping from source text → taxonomy

## Taxonomy Categories (v1)

`FailureEvent.category` enum:

- `assertion`
- `scoreboard`
- `protocol`
- `timeout`
- `xprop`
- `compile`
- `elab`
- `runtime`
- `unknown`

## Severity Mapping (v1)

### UVM Severity Normalization

Map to:

- `UVM_INFO` → `info`
- `UVM_WARNING` → `warning`
- `UVM_ERROR` → `error`
- `UVM_FATAL` → `fatal`

If a simulator prefixes errors differently (e.g., `*E`, in Xcelium), map to `error` unless fatal keywords exist.

### cocotb Severity Normalization

- Exception in test → `error`
- Explicit assertion failure → `fail` at test level, but failure events often still `error` unless you distinguish "check failure" vs "infrastructure error"

**Recommended**:
- If message matches `AssertionError`, `ScoreboardMismatch`, or user "expect" failure → `error` but category `scoreboard`/`protocol`/`assertion` as appropriate
- If matches `ImportError`, `RuntimeError` at harness, `SimulatorError` → `runtime` + severity `fatal` (configurable)

---

## Category Mapping Rules (ordered, first match wins)

### Rule Group A: Compile / Elaboration (highest priority)

#### 1. Compile

**Patterns**:
- `Compilation failed`
- `Error-[A-Z0-9]+` with `compile`
- `vlog-` / `xmvlog` errors
- `Syntax error`, `unexpected token`, `Undefined variable` in compile context

**Category**: `compile`  
**Tags**: `["compile"]` + vendor tags

#### 2. Elaboration

**Patterns**:
- `Elaboration failed`
- `Unresolved reference` (during elab)
- `Cannot find instance` / `binding failed`
- `Top module not found`

**Category**: `elab`  
**Tags**: `["elab"]`

### Rule Group B: Assertions

#### 3. Assertion Failures

**Patterns**:
- `ASSERTION FAILED`
- `SVA` and `failed`
- `assert property` failure messages
- **Vendor-specific**:
  - Questa: `** Error: (vsim-*)` with assertion wording
  - VCS: `Assertion failure` / `$assertoff` contexts

**Category**: `assertion`  
**Tags**: `["assertion", "sva"]` + protocol tags if detectable (AXI/APB/etc.)

If an assertion name is captured, attach it to:
- `AssertionFailure.assertion_id` (when resolvable)
- `FailureEvent.tags` += `["assert:<name>"]` (bounded)

### Rule Group C: Timeouts / Deadlocks

#### 4. Timeout

**Patterns**:
- `TIMEOUT`
- `watchdog`
- `No activity for`
- `objection timeout`
- `phase timeout`
- `simulation time limit reached`

**Category**: `timeout`  
**Tags**: `["timeout"]` + phase tags if known (e.g., `phase:run`)

### Rule Group D: X-Propagation / Unknowns

#### 5. Xprop / X-Check

**Patterns**:
- `X-propagation`
- `X-check`
- `Unknown value X`
- `has Xs`
- `xrun: *E` combined with X warnings (vendor-specific)

**Category**: `xprop`  
**Tags**: `["xprop"]`

### Rule Group E: Scoreboard / Data Mismatches

#### 6. Scoreboard Mismatch

**Patterns**:
- `scoreboard` and (`mismatch`|`compare failed`|`unexpected`|`expected`)
- `DATA MISMATCH`
- `CRC mismatch` (often protocol too; see tags)
- `sequence item mismatch`

**Category**: `scoreboard`  
**Tags**: `["scoreboard"]` + protocol tags if detectable

### Rule Group F: Protocol Violations (when explicit)

#### 7. Protocol

**Patterns**:
- `protocol violation`
- `handshake violation`
- `illegal transition`
- `unexpected response` (when not scoreboard compare)
- `BRESP`/`RRESP` error codes in AXI monitors
- `APB PSLVERR` in monitor

**Category**: `protocol`  
**Tags**: `["protocol"]` + protocol name tags

### Rule Group G: Runtime/Infrastructure

#### 8. Runtime

**Patterns**:
- `segmentation fault`
- `core dumped`
- `Simulator terminated`
- Python traceback that indicates harness failure
- `Out of memory`
- `License checkout failed`

**Category**: `runtime`  
**Severity**: `fatal` for crashes/license failures; otherwise `error`  
**Tags**: `["runtime"]`

### Default

#### 9. Unknown

**Category**: `unknown`  
**Tags**: derived from heuristic keyword extraction (bounded)

---

## Tagging System (v1)

### Standard Tags (recommended)

- **Vendor**: `vcs`, `questa`, `xcelium`, `verilator`, `riviera`
- **Framework**: `uvm`, `cocotb`
- **Protocol**: `axi4`, `ahb`, `apb`, `pcie`, `usb`, `jtag`, `i2c`, `spi`, `gpio`
- **Phase**: `phase:build`, `phase:connect`, `phase:run`, `phase:shutdown`
- **Component role**: `driver`, `monitor`, `scoreboard`, `sequencer`

### Protocol Detection Heuristics

If message contains:

- `AXI` or `AWVALID`/`WREADY`/`BRESP` → tag `axi4`
- `PADDR`/`PSEL`/`PREADY`/`PSLVERR` → tag `apb`
- `HADDR`/`HREADY`/`HRESP` → tag `ahb`
- `LTSSM`, `TS1`, `TS2` → tag `pcie`
- `LFPS`, `PIPE`, `U0`/`U1`/`U2` → tag `usb`
- `TMS`, `TCK`, `TDO`, `TDI` → tag `jtag`

### Bounded Tagging

- **Max tags per failure**: 20
- **Prefer deterministic ordering**: `[category/framework/protocol/vendor/phase/component_role/other]`

---

## Evidence Linkage Policy

When a taxonomy decision is made, the indexer may store:

- `taxonomy_reason`: a short code like `RULE_ASSERTION_VENDOR_QUES` (optional internal field)
- This reason is not required to be exposed via MCP in v1, but helps debugging

---

## Implementation Reference

See `sentinel_dv/taxonomy_engine.py` for the canonical implementation.
