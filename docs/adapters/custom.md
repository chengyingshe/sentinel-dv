# Custom Adapters

Create custom adapters to support additional log formats, simulators, or frameworks.

## Adapter Overview

Adapters extract structured data from verification artifacts:

- **Log Adapters**: Parse test logs (UVM, cocotb, custom)
- **Coverage Adapters**: Parse coverage reports (XML, DAT, UCDB)
- **Assertion Adapters**: Extract assertion definitions from HDL
- **Waveform Adapters**: Generate waveform summaries

## Adapter Interface

### Base Adapter

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseAdapter(ABC):
    """Base adapter interface."""
    
    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Check if adapter can handle this file."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse file and return structured data."""
        pass
    
    @abstractmethod
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate parsed data."""
        pass
```

---

## Log Adapter Example

### Custom UVM Adapter

```python
from sentinel_dv.adapters import LogAdapter
import re

class CustomUVMAdapter(LogAdapter):
    """Parse custom UVM log format."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this is a UVM log."""
        with open(file_path) as f:
            first_line = f.readline()
            return "UVM_INFO" in first_line or "UVM_ERROR" in first_line
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse UVM log file."""
        test_name = None
        framework = "uvm"
        status = "pass"
        duration_ms = None
        failures = []
        
        with open(file_path) as f:
            for line in f:
                # Extract test name
                if match := re.match(r"UVM_INFO.*UVM_TEST_TOP\s+\[(\w+)\]", line):
                    test_name = match.group(1)
                
                # Extract errors
                if match := re.match(
                    r"UVM_ERROR\s+@\s+(\d+)ns:\s+([^\[]+)\[([^\]]+)\]\s+(.*)",
                    line
                ):
                    time_ns = int(match.group(1))
                    scope = match.group(2).strip()
                    category = match.group(3).strip()
                    message = match.group(4).strip()
                    
                    failures.append({
                        "type": "uvm_error",
                        "time_ns": time_ns,
                        "scope": scope,
                        "category": self._map_category(category),
                        "severity": "error",
                        "message": message
                    })
                    status = "fail"
                
                # Extract duration
                if match := re.match(r".*Simulation complete.*(\d+)ms", line):
                    duration_ms = int(match.group(1))
        
        return {
            "test_name": test_name,
            "framework": framework,
            "status": status,
            "duration_ms": duration_ms,
            "failures": failures
        }
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate parsed data."""
        required = ["test_name", "framework", "status"]
        return all(k in data for k in required)
    
    def _map_category(self, uvm_category: str) -> str:
        """Map UVM category to standard category."""
        mapping = {
            "PROTOCOL": "protocol",
            "FUNCTIONAL": "functional",
            "TIMING": "timing",
            "MONITOR": "functional",
            "DRIVER": "functional",
        }
        return mapping.get(uvm_category, "functional")
```

---

## Coverage Adapter Example

### XML Coverage Adapter

```python
from sentinel_dv.adapters import CoverageAdapter
import xml.etree.ElementTree as ET

class XMLCoverageAdapter(CoverageAdapter):
    """Parse XML coverage format."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this is XML coverage."""
        return file_path.endswith(".xml") and "coverage" in file_path
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse XML coverage file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        coverage_data = {
            "kind": "functional",
            "overall_percentage": 0.0,
            "bins_total": 0,
            "bins_covered": 0,
            "covergroups": []
        }
        
        # Parse covergroups
        for cg in root.findall(".//covergroup"):
            cg_name = cg.get("name")
            cg_instance = cg.get("instance")
            
            coverpoints = []
            for cp in cg.findall("coverpoint"):
                cp_name = cp.get("name")
                bins = []
                
                for bin_elem in cp.findall("bin"):
                    bin_name = bin_elem.get("name")
                    count = int(bin_elem.get("count", 0))
                    goal = int(bin_elem.get("goal", 100))
                    
                    bins.append({
                        "name": bin_name,
                        "count": count,
                        "goal": goal,
                        "covered": count >= goal
                    })
                    
                    coverage_data["bins_total"] += 1
                    if count >= goal:
                        coverage_data["bins_covered"] += 1
                
                coverpoints.append({
                    "name": cp_name,
                    "bins": bins
                })
            
            coverage_data["covergroups"].append({
                "name": cg_name,
                "instance": cg_instance,
                "coverpoints": coverpoints
            })
        
        # Calculate overall percentage
        if coverage_data["bins_total"] > 0:
            coverage_data["overall_percentage"] = (
                coverage_data["bins_covered"] / coverage_data["bins_total"] * 100
            )
        
        return coverage_data
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate coverage data."""
        required = ["kind", "overall_percentage", "bins_total", "bins_covered"]
        return all(k in data for k in required)
```

---

## Assertion Adapter Example

### SystemVerilog Assertion Adapter

```python
from sentinel_dv.adapters import AssertionAdapter
import re

class SVAAdapter(AssertionAdapter):
    """Extract SVA assertions from SystemVerilog files."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this is a SystemVerilog file."""
        return file_path.endswith((".sv", ".svh"))
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse SystemVerilog assertions."""
        assertions = []
        current_module = None
        
        with open(file_path) as f:
            content = f.read()
        
        # Find module name
        if match := re.search(r"module\s+(\w+)", content):
            current_module = match.group(1)
        
        # Find assertions
        assertion_pattern = re.compile(
            r"(\w+):\s*assert\s+property\s*\((.*?)\)\s*"
            r"else\s+\$error\((.*?)\);",
            re.MULTILINE | re.DOTALL
        )
        
        for match in assertion_pattern.finditer(content):
            name = match.group(1)
            property_expr = match.group(2).strip()
            error_msg = match.group(3).strip().strip('"')
            
            # Determine severity
            severity = "error"
            if "$warning" in content[match.start():match.end()]:
                severity = "warning"
            elif "$fatal" in content[match.start():match.end()]:
                severity = "fatal"
            
            # Determine category
            category = self._infer_category(name, error_msg)
            
            assertions.append({
                "name": name,
                "scope": current_module or "unknown",
                "file": file_path,
                "line": content[:match.start()].count("\n") + 1,
                "severity": severity,
                "category": category,
                "intent": error_msg,
                "property": property_expr,
                "tags": self._extract_tags(name, error_msg)
            })
        
        return {"assertions": assertions}
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate assertion data."""
        return "assertions" in data
    
    def _infer_category(self, name: str, message: str) -> str:
        """Infer category from assertion name/message."""
        text = f"{name} {message}".lower()
        
        if any(kw in text for kw in ["protocol", "handshake", "valid", "ready"]):
            return "protocol"
        elif any(kw in text for kw in ["timing", "delay", "clock"]):
            return "timing"
        elif any(kw in text for kw in ["power", "voltage"]):
            return "power"
        else:
            return "functional"
    
    def _extract_tags(self, name: str, message: str) -> list[str]:
        """Extract tags from assertion."""
        tags = []
        text = f"{name} {message}".lower()
        
        # Protocol tags
        if "axi" in text:
            tags.append("axi4")
        if "pcie" in text:
            tags.append("pcie")
        
        # Type tags
        if "handshake" in text:
            tags.append("handshake")
        if "data" in text:
            tags.append("data-integrity")
        
        return tags
```

---

## Waveform Adapter Example

### VCD Adapter

```python
from sentinel_dv.adapters import WaveformAdapter

class VCDAdapter(WaveformAdapter):
    """Extract summary from VCD waveform."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this is a VCD file."""
        return file_path.endswith(".vcd")
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse VCD waveform summary."""
        signals = {}
        current_time = 0
        
        with open(file_path) as f:
            # Skip header
            for line in f:
                if line.startswith("$enddefinitions"):
                    break
                
                # Extract signal definitions
                if line.startswith("$var"):
                    parts = line.split()
                    signal_id = parts[3]
                    signal_name = parts[4]
                    signals[signal_id] = {
                        "name": signal_name,
                        "toggles": 0,
                        "last_value": None
                    }
            
            # Count toggles
            for line in f:
                if line.startswith("#"):
                    current_time = int(line[1:])
                elif len(line) > 1:
                    value = line[0]
                    signal_id = line[1:].strip()
                    
                    if signal_id in signals:
                        if signals[signal_id]["last_value"] != value:
                            signals[signal_id]["toggles"] += 1
                            signals[signal_id]["last_value"] = value
        
        return {
            "format": "vcd",
            "end_time_ns": current_time,
            "signal_count": len(signals),
            "signals": [
                {
                    "name": s["name"],
                    "toggles": s["toggles"]
                }
                for s in signals.values()
            ]
        }
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate waveform data."""
        return "format" in data and "signals" in data
```

---

## Registering Custom Adapters

### Configuration

```python
# config.yaml
adapters:
  log:
    - module: my_adapters.custom_uvm
      class: CustomUVMAdapter
      priority: 10
  
  coverage:
    - module: my_adapters.xml_coverage
      class: XMLCoverageAdapter
      priority: 10
  
  assertion:
    - module: my_adapters.sva
      class: SVAAdapter
      priority: 10
  
  waveform:
    - module: my_adapters.vcd
      class: VCDAdapter
      priority: 10
```

---

### Python API

```python
from sentinel_dv import SentinelDV
from my_adapters import CustomUVMAdapter, XMLCoverageAdapter

client = SentinelDV(db_path="./sentinel_db")

# Register adapters
client.register_adapter("log", CustomUVMAdapter())
client.register_adapter("coverage", XMLCoverageAdapter())

# Use custom adapters
client.index_run(
    run_id="R20260125_143000",
    log_dir="./results"
)
```

---

## Adapter Priority

Adapters are tried in priority order:

```python
class AdapterRegistry:
    """Registry for adapters."""
    
    def __init__(self):
        self.adapters = {
            "log": [],
            "coverage": [],
            "assertion": [],
            "waveform": []
        }
    
    def register(self, adapter_type: str, adapter: BaseAdapter, priority: int = 10):
        """Register an adapter with priority."""
        self.adapters[adapter_type].append((priority, adapter))
        self.adapters[adapter_type].sort(key=lambda x: x[0], reverse=True)
    
    def get_adapter(self, adapter_type: str, file_path: str) -> BaseAdapter | None:
        """Get adapter that can handle this file."""
        for priority, adapter in self.adapters[adapter_type]:
            if adapter.can_handle(file_path):
                return adapter
        return None
```

**Priority Guidelines**:
- `20`: Highly specific formats (e.g., proprietary simulator)
- `10`: Standard formats (e.g., UVM, JUnit XML)
- `5`: Generic formats (e.g., text logs)
- `1`: Fallback adapters

---

## Testing Adapters

### Unit Tests

```python
import pytest
from my_adapters import CustomUVMAdapter

def test_uvm_adapter_can_handle():
    adapter = CustomUVMAdapter()
    assert adapter.can_handle("test.log")
    assert not adapter.can_handle("test.xml")

def test_uvm_adapter_parse():
    adapter = CustomUVMAdapter()
    data = adapter.parse("fixtures/uvm_test.log")
    
    assert data["test_name"] == "axi_burst_test"
    assert data["framework"] == "uvm"
    assert data["status"] == "fail"
    assert len(data["failures"]) == 2

def test_uvm_adapter_validate():
    adapter = CustomUVMAdapter()
    
    valid_data = {
        "test_name": "test",
        "framework": "uvm",
        "status": "pass"
    }
    assert adapter.validate(valid_data)
    
    invalid_data = {"test_name": "test"}
    assert not adapter.validate(invalid_data)
```

---

### Integration Tests

```python
from sentinel_dv import SentinelDV
from my_adapters import CustomUVMAdapter

def test_adapter_integration():
    client = SentinelDV(db_path=":memory:")
    client.register_adapter("log", CustomUVMAdapter())
    
    # Index with custom adapter
    client.index_run(
        run_id="R_test",
        log_dir="fixtures/test_run"
    )
    
    # Verify data
    tests = client.tests.list(run_id="R_test")
    assert tests.total_items > 0
    assert tests.items[0].framework == "uvm"
```

---

## Best Practices

### 1. Robust Parsing

```python
def parse(self, file_path: str) -> dict[str, Any]:
    """Parse log file robustly."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return self._parse_content(f)
    except UnicodeDecodeError:
        # Fallback to latin-1
        with open(file_path, encoding="latin-1") as f:
            return self._parse_content(f)
    except Exception as e:
        # Log error but don't crash
        logger.error(f"Failed to parse {file_path}: {e}")
        return self._default_data()
```

---

### 2. Incremental Parsing

```python
def parse(self, file_path: str) -> dict[str, Any]:
    """Parse large files incrementally."""
    data = self._default_data()
    
    with open(file_path) as f:
        for line in f:
            self._process_line(line, data)
            
            # Don't load entire file into memory
            if len(data["failures"]) > 1000:
                break  # Limit failures
    
    return data
```

---

### 3. Error Handling

```python
def can_handle(self, file_path: str) -> bool:
    """Check if adapter can handle file."""
    try:
        with open(file_path) as f:
            header = f.read(1024)  # Only read header
            return self._check_header(header)
    except Exception:
        return False  # Can't handle if can't read
```

---

### 4. Performance

```python
import re

class FastAdapter(BaseAdapter):
    def __init__(self):
        # Compile regexes once
        self.error_pattern = re.compile(r"ERROR: (.*)")
        self.test_pattern = re.compile(r"TEST: (\w+)")
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Use compiled regexes for speed."""
        with open(file_path) as f:
            for line in f:
                if match := self.error_pattern.match(line):
                    # Process error
                    pass
```

---

## Examples

### Complete Custom Adapter

See [UVM Adapter](uvm.md) for a complete example of a production-quality adapter.

### Adapter Template

```python
from sentinel_dv.adapters import BaseAdapter
from typing import Any

class MyCustomAdapter(BaseAdapter):
    """Adapter for <format> format."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this adapter can handle the file."""
        # TODO: Implement detection logic
        return False
    
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse file and extract structured data."""
        # TODO: Implement parsing logic
        return {}
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate parsed data structure."""
        # TODO: Implement validation logic
        return True
```

---

## Next Steps

- [UVM Adapter →](uvm.md) - Complete UVM adapter implementation
- [cocotb Adapter →](cocotb.md) - cocotb JUnit XML adapter
- [Architecture →](../architecture/overview.md) - Understand adapter architecture
