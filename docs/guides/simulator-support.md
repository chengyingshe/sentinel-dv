# Simulator Support

Sentinel DV supports verification artifacts from major commercial and open-source simulators.

## Supported Simulators

### VCS (Synopsys)

**Version Support**: VCS 2019.06 and later

**Supported Artifacts**:
- UVM logs (`simv.log`, custom log files)
- Coverage databases (UCDB format)
- Assertion reports (FSDB assertions)
- Waveforms (VPD, FSDB)

**Configuration**:
```yaml
simulators:
  vcs:
    log_patterns:
      - "**/simv.log"
      - "**/run.log"
    coverage_patterns:
      - "**/*.vdb"
      - "**/coverage.xml"
    assertion_patterns:
      - "**/assertions.rpt"
    waveform_patterns:
      - "**/*.vpd"
      - "**/*.fsdb"
```

**Indexing Example**:
```bash
sentinel-dv index \
  --simulator vcs \
  --log-dir ./results/vcs_run \
  --coverage-dir ./coverage/vcs \
  --output ./sentinel_db
```

**Known Limitations**:
- FSDB parsing requires Synopsys libraries
- UCDB conversion to XML recommended for coverage

---

### Xcelium (Cadence)

**Version Support**: Xcelium 19.09 and later (formerly IES/Incisive)

**Supported Artifacts**:
- UVM logs (`irun.log`, custom log files)
- Coverage databases (IMC format)
- Assertion reports
- Waveforms (SHM)

**Configuration**:
```yaml
simulators:
  xcelium:
    log_patterns:
      - "**/irun.log"
      - "**/xrun.log"
    coverage_patterns:
      - "**/cov_work/**/*.ucm"
      - "**/coverage.xml"
    assertion_patterns:
      - "**/assertions.log"
    waveform_patterns:
      - "**/*.shm"
```

**Indexing Example**:
```bash
sentinel-dv index \
  --simulator xcelium \
  --log-dir ./results/xcelium_run \
  --coverage-dir ./cov_work \
  --output ./sentinel_db
```

**Coverage Export**:
```bash
# Export IMC coverage to XML
imc -exec merge -out merged.ucm *.ucm
imc -exec report -format xml -out coverage.xml merged.ucm
```

---

### Questa (Mentor/Siemens)

**Version Support**: Questa 2020.1 and later

**Supported Artifacts**:
- UVM logs (`transcript`, custom log files)
- Coverage databases (UCDB format)
- Assertion reports
- Waveforms (WLF)

**Configuration**:
```yaml
simulators:
  questa:
    log_patterns:
      - "**/transcript"
      - "**/vsim.log"
    coverage_patterns:
      - "**/*.ucdb"
      - "**/coverage.xml"
    assertion_patterns:
      - "**/assertions.rpt"
    waveform_patterns:
      - "**/*.wlf"
```

**Indexing Example**:
```bash
sentinel-dv index \
  --simulator questa \
  --log-dir ./results/questa_run \
  --coverage-db ./coverage.ucdb \
  --output ./sentinel_db
```

**Coverage Export**:
```bash
# Convert UCDB to XML
vcover report -format xml -output coverage.xml coverage.ucdb
```

---

### Verilator (Open Source)

**Version Support**: Verilator 4.0 and later

**Supported Artifacts**:
- Log files (stdout/stderr)
- Coverage reports (DAT format)
- VCD waveforms
- Custom assertion logs

**Configuration**:
```yaml
simulators:
  verilator:
    log_patterns:
      - "**/run.log"
      - "**/stdout.txt"
    coverage_patterns:
      - "**/coverage.dat"
    waveform_patterns:
      - "**/*.vcd"
    assertion_patterns:
      - "**/assertions.log"
```

**Indexing Example**:
```bash
sentinel-dv index \
  --simulator verilator \
  --log-dir ./obj_dir \
  --coverage ./coverage.dat \
  --output ./sentinel_db
```

**Coverage Generation**:
```bash
# Compile with coverage
verilator --coverage --exe --build test.sv sim_main.cpp

# Run simulation
./obj_dir/Vtest

# Generate coverage report
verilator_coverage --write coverage.dat coverage.dat
```

---

## Framework Support

### UVM (Universal Verification Methodology)

**Supported Versions**:
- UVM 1.1d
- UVM 1.2 (IEEE 1800.2-2017)
- UVM 2020 (IEEE 1800.2-2020)

**Extracted Information**:
- Test hierarchy and topology
- Component instances
- Sequence execution
- Phase execution timing
- UVM reports (INFO, WARNING, ERROR, FATAL)
- Configuration database settings
- Factory overrides

**Log Parsing**:
```python
# UVM report format
UVM_INFO @ 1000ns: uvm_test_top.env.agent [MONITOR] Transaction detected
UVM_ERROR @ 1250ns: uvm_test_top.env.agent.monitor [PROTOCOL] AXI handshake violation

# Extracted as FailureEvent
{
  "severity": "error",
  "time_ns": 1250,
  "scope": "uvm_test_top.env.agent.monitor",
  "category": "protocol",
  "message": "AXI handshake violation"
}
```

---

### cocotb (Python-based)

**Supported Versions**: cocotb 1.5+

**Supported Artifacts**:
- JUnit XML test results
- Python log files
- VCD waveforms
- Custom assertion logs

**Configuration**:
```yaml
frameworks:
  cocotb:
    junit_patterns:
      - "**/results.xml"
    log_patterns:
      - "**/cocotb.log"
    waveform_patterns:
      - "**/*.vcd"
```

**Example Test Result**:
```xml
<!-- results.xml -->
<testsuite name="axi_tests" tests="10" failures="2">
  <testcase classname="axi_tests" name="test_write_burst" time="0.152">
    <failure message="Assertion failed: AWVALID not stable">
      axi_if.py:145: AssertionError
    </failure>
  </testcase>
</testsuite>
```

**Indexing**:
```bash
sentinel-dv index \
  --framework cocotb \
  --junit-xml ./results.xml \
  --log-dir ./logs \
  --output ./sentinel_db
```

---

### SystemVerilog Unit Testing

**Supported Frameworks**:
- SVUnit
- UVMT (UVM Testbench)

**Supported Artifacts**:
- Test results (custom format)
- Assertion logs
- Coverage reports

**Configuration**:
```yaml
frameworks:
  sv_unit:
    result_patterns:
      - "**/run.log"
    assertion_patterns:
      - "**/assertions.log"
```

---

## Coverage Formats

### Functional Coverage

**Supported Formats**:
- UVM covergroups (extracted from logs)
- XML coverage reports
- Custom CSV formats

**Example XML**:
```xml
<coverage>
  <covergroup name="axi_burst_cg" instance="env.cov">
    <coverpoint name="burst_type">
      <bin name="FIXED" count="10" goal="100"/>
      <bin name="INCR" count="50" goal="100"/>
      <bin name="WRAP" count="15" goal="100"/>
    </coverpoint>
  </covergroup>
</coverage>
```

---

### Code Coverage

**Supported Metrics**:
- Line coverage
- Branch coverage
- Toggle coverage
- FSM coverage
- Expression coverage

**Export Commands**:

**VCS**:
```bash
urg -dir simv.vdb -format text -report coverage
```

**Xcelium**:
```bash
imc -exec report -format xml -out coverage.xml merged.ucm
```

**Questa**:
```bash
vcover report -format xml -output coverage.xml coverage.ucdb
```

**Verilator**:
```bash
verilator_coverage --write coverage.info coverage.dat
```

---

### Assertion Coverage

**Supported Formats**:
- SVA assertion reports
- PSL assertion reports
- Custom assertion logs

**Example Report**:
```
Assertion Coverage Summary
==========================
Total Assertions: 50
Covered: 39
Percentage: 78.0%

Uncovered Assertions:
  - axi_master_if.rare_burst_type_check
  - pcie_if.power_state_transition_check
```

---

## Waveform Integration

### VCD (Value Change Dump)

**Support**: Full VCD parsing for assertions and timing analysis

**Example**:
```vcd
$date
  January 25, 2026
$end
$timescale 1ns $end
$var wire 1 ! clk $end
$var wire 1 " awvalid $end
$var wire 1 # awready $end
#0
0!
0"
0#
#10
1!
1"
#20
0!
1#
```

---

### VPD (VCS)

**Support**: Read-only waveform summary extraction

**Configuration**:
```yaml
waveforms:
  vpd:
    extract_summary: true
    signal_patterns:
      - "*.awvalid"
      - "*.awready"
```

---

### FSDB (Synopsys)

**Support**: Requires Synopsys Verdi libraries

**Setup**:
```bash
export LD_LIBRARY_PATH=$VERDI_HOME/share/FsdbReader/LINUX64
sentinel-dv index --waveform-format fsdb ...
```

---

### SHM (Cadence)

**Support**: Read-only waveform summary extraction

**Configuration**:
```yaml
waveforms:
  shm:
    extract_summary: true
```

---

### WLF (Questa)

**Support**: Waveform summary via ModelSim API

**Setup**:
```bash
export QUESTA_HOME=/path/to/questa
sentinel-dv index --waveform-format wlf ...
```

---

## Best Practices

### 1. Consistent Directory Structure

```
verification/
├── runs/
│   ├── R20260125_143000/
│   │   ├── logs/
│   │   │   └── run.log
│   │   ├── coverage/
│   │   │   └── coverage.xml
│   │   ├── waveforms/
│   │   │   └── waves.vcd
│   │   └── assertions/
│   │       └── assertions.rpt
│   └── R20260125_150000/
│       └── ...
└── sentinel_db/
```

### 2. Simulator-Specific Scripts

**VCS Indexing**:
```bash
#!/bin/bash
# index_vcs.sh
sentinel-dv index \
  --simulator vcs \
  --log-dir $1/logs \
  --coverage-dir $1/coverage \
  --waveform-dir $1/waveforms \
  --run-id $(basename $1) \
  --output ./sentinel_db
```

**Questa Indexing**:
```bash
#!/bin/bash
# index_questa.sh
sentinel-dv index \
  --simulator questa \
  --log-dir $1 \
  --coverage-db $1/coverage.ucdb \
  --run-id $(basename $1) \
  --output ./sentinel_db
```

### 3. Coverage Export Automation

```makefile
# Makefile
.PHONY: coverage-export

coverage-export:
ifeq ($(SIMULATOR),vcs)
	urg -dir simv.vdb -format xml -report coverage.xml
else ifeq ($(SIMULATOR),questa)
	vcover report -format xml -output coverage.xml coverage.ucdb
else ifeq ($(SIMULATOR),xcelium)
	imc -exec report -format xml -out coverage.xml merged.ucm
endif
```

### 4. Multi-Simulator Support

```python
# config.yaml
simulators:
  - name: vcs
    enabled: true
    log_pattern: "**/simv.log"
  - name: questa
    enabled: true
    log_pattern: "**/transcript"
  - name: xcelium
    enabled: true
    log_pattern: "**/irun.log"

# Auto-detect simulator
def detect_simulator(log_file: str) -> str:
    with open(log_file) as f:
        content = f.read(1000)
        if "Chronologic VCS" in content:
            return "vcs"
        elif "Questa" in content or "ModelSim" in content:
            return "questa"
        elif "xcelium" in content or "irun" in content:
            return "xcelium"
        elif "Verilator" in content:
            return "verilator"
    return "unknown"
```

## Troubleshooting

### VCS Issues

**Problem**: FSDB files not readable
```
Error: Cannot load FSDB reader library
```

**Solution**:
```bash
export LD_LIBRARY_PATH=$VERDI_HOME/share/FsdbReader/LINUX64:$LD_LIBRARY_PATH
```

---

### Questa Issues

**Problem**: UCDB file locked
```
Error: coverage.ucdb is locked by another process
```

**Solution**:
```bash
# Close Questa GUI
# Or export to XML first
vcover report -format xml -output coverage.xml coverage.ucdb
```

---

### Xcelium Issues

**Problem**: Coverage database not found
```
Error: Cannot find cov_work directory
```

**Solution**:
```bash
# Ensure -coverage flag during simulation
xrun -coverage all test.sv

# Verify cov_work exists
ls -la cov_work/
```

---

### Verilator Issues

**Problem**: No coverage data
```
Warning: coverage.dat is empty
```

**Solution**:
```bash
# Ensure --coverage flag during verilator compilation
verilator --coverage --exe --build test.sv sim_main.cpp

# Coverage is only collected if simulation runs
./obj_dir/Vtest
```

## Next Steps

- [Performance Guide →](performance.md) - Optimize indexing and queries
- [Custom Adapters →](../adapters/custom.md) - Support additional formats
- [Getting Started →](../getting-started/quick-start.md) - Basic usage examples
