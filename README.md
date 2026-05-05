# logslice

Stream and filter structured JSON logs from multiple sources with a unified query syntax.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
pip install git+https://github.com/yourname/logslice.git
```

---

## Usage

```bash
# Stream logs from a file and filter by level
logslice stream app.log --where "level=error"

# Tail multiple sources simultaneously
logslice stream app.log worker.log --follow

# Filter with multiple conditions and pretty-print output
logslice stream app.log --where "level=error" --where "service=api" --pretty

# Query a specific time range
logslice stream app.log --after "2024-01-15T10:00:00" --before "2024-01-15T11:00:00"
```

**Python API:**

```python
from logslice import LogStream

stream = LogStream("app.log", "worker.log")
for entry in stream.where(level="error", service="api").follow():
    print(entry["message"])
```

---

## Query Syntax

| Operator | Example | Description |
|----------|---------|-------------|
| `=` | `level=error` | Exact match |
| `~=` | `message~=timeout` | Contains substring |
| `>=` | `status>=500` | Numeric comparison |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)