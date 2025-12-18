# **Data Stream Python**
This snippet is meant to demonstrate **how to build a simple data-stream processing pipeline in Python** — reading data line-by-line from an input stream, transforming it, and writing it to an output stream.

However, it’s best understood as an *educational example*. I’ll explain:

1. **What it is trying to do (conceptually)**
2. **How it works line by line**

---

## 1. What this code is about (big picture)

This function is an example of a **stream processor**:

```
reader  →  converter  →  writer
```

* **reader**: a file-like object you can iterate over (e.g., a file, `sys.stdin`)
* **converter**: a function that transforms each line (e.g., uppercase, strip whitespace, parse JSON)
* **writer**: a file-like object you can write to (e.g., a file, `sys.stdout`)

It processes data **line by line**, which is memory-efficient and commonly used in:

* log processing
* ETL pipelines
* command-line tools
* streaming large files

---

## 2. What the function is intended to do

```python
def processor(reader, converter, writer) -> int:
```

**Intent**:

* Read lines from `reader`
* Apply `converter(line)` to each line
* Write the result to `writer`
* Return how many lines were processed

---

### Step-by-step logic

```python
if not callable(converter):
    raise TypeError("converter must be callable")
```

✔ Ensures the transformer is a function.

---

```python
count = 0
```

Keeps track of how many lines were processed.

---

```python
for line in reader:
```

Iterates over the input stream **line by line**.

---

```python
writer.write(converter(line))
```

* Passes the line through the converter
* Writes the transformed output

---

```python
except Exception as e:
    raise RuntimeError(f"processor failed on line {count + 1}") from e
```

Wraps any error with context (which line failed).

---

```python
writer.flush()
return count
```

* Forces output to be written immediately
* Returns the number of processed lines

---

## 3. Example usage

```python
import sys

def to_upper(line: str) -> str:
    return line.upper()

processor(sys.stdin, to_upper, sys.stdout)
```

This would:

* Read text from standard input
* Convert each line to uppercase
* Write it to standard output

---

### In one sentence

👉 **This code demonstrates a streaming data pipeline pattern in Python: read → transform → write, line by line, using file-like objects.**

---

# A practical command-line tool to architectural comparisons.

---

# 1. Turn it into a command-line tool

Build a **Unix-style CLI filter** that:

* Reads from a file or `stdin`
* Writes to a file or `stdout`
* Applies a chosen transformation

## Example usage

```bash
# uppercase stdin → stdout
python processor.py upper

# read file, write file
python processor.py strip input.txt output.txt

# pipeline usage
cat access.log | python processor.py redact_ip | sort
```

---

## `processor.py`

```python
#!/usr/bin/env python3
from __future__ import annotations
import sys
import argparse
from typing import Callable, TextIO


# -------------------------
# Core stream processor
# -------------------------
def processor(
    reader: TextIO,
    converter: Callable[[str], str],
    writer: TextIO
) -> int:
    count = 0
    for line in reader:
        try:
            writer.write(converter(line))
        except Exception as e:
            raise RuntimeError(f"processor failed on line {count + 1}") from e
        count += 1

    writer.flush()
    return count


# -------------------------
# Converters
# -------------------------
def upper(line: str) -> str:
    return line.upper()


def lower(line: str) -> str:
    return line.lower()


def strip(line: str) -> str:
    return line.strip() + "\n"


def redact_ip(line: str) -> str:
    import re
    return re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "[REDACTED_IP]", line)


CONVERTERS = {
    "upper": upper,
    "lower": lower,
    "strip": strip,
    "redact_ip": redact_ip,
}


# -------------------------
# CLI
# -------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream text processor (stdin → transform → stdout)"
    )
    parser.add_argument(
        "converter",
        choices=CONVERTERS.keys(),
        help="Transformation to apply",
    )
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("output", nargs="?", help="Output file (default: stdout)")

    args = parser.parse_args()

    reader = open(args.input) if args.input else sys.stdin
    writer = open(args.output, "w") if args.output else sys.stdout

    try:
        count = processor(reader, CONVERTERS[args.converter], writer)
    finally:
        if args.input:
            reader.close()
        if args.output:
            writer.close()

    print(f"Processed {count} lines", file=sys.stderr)


if __name__ == "__main__":
    main()
```

This behaves like standard Unix tools (`sed`, `awk`, `tr`).

---

# 2. Real-world use cases

This pattern is **extremely common** in production systems.

## A. Log processing

```bash
cat nginx.log | python processor.py redact_ip > safe.log
```

* Remove PII
* Normalize formats
* Filter errors

Used in:

* observability pipelines
* compliance tools
* security audits

---

## B. ETL (Extract → Transform → Load)

```bash
python processor.py strip raw_data.txt cleaned_data.txt
```

* Extract: file or stream
* Transform: normalize, validate
* Load: database import, CSV, JSON

This is the *core* idea behind tools like:

* Apache Beam
* Airflow tasks
* Kafka consumers

---

## C. Data validation & sanitization

```python
def validate(line: str) -> str:
    if "," not in line:
        raise ValueError("invalid CSV")
    return line
```

Fail fast with clear line numbers.

---

## D. Unix-style composability

```bash
cat big.txt \
| python processor.py lower \
| grep error \
| sort \
| uniq -c
```

Small tools, chained together.

---

## E. Testing & mocking

Because `reader` and `writer` are just **file-like objects**, you can test with:

```python
from io import StringIO

inp = StringIO("a\nb\n")
out = StringIO()

processor(inp, upper, out)
assert out.getvalue() == "A\nB\n"
```

No filesystem needed.

---

# 3. Comparison: plain streams vs generators vs async streams

This is where architecture matters.

---

## A. Current approach (iterator over TextIO)

### Characteristics

✔ Simple
✔ File & stdin compatible
✔ Memory efficient
✘ Pull-based only
✘ Blocking I/O

```python
for line in reader:
    writer.write(converter(line))
```

### Best for:

* Files
* CLI tools
* Batch processing
* Logs

---

## B. Generator-based pipeline

Instead of writing directly, you **yield transformed data**.

```python
def transform(lines):
    for line in lines:
        yield line.upper()
```

Usage:

```python
for out_line in transform(sys.stdin):
    sys.stdout.write(out_line)
```

### Pros

✔ Composable
✔ Easy to chain
✔ Testable

### Cons

✘ Still blocking
✘ Output control handled elsewhere

### When to use

* Complex pipelines
* Multiple transformations
* Functional-style code

---

## C. Async streams (`async for`)

```python
async def processor(reader, writer):
    async for line in reader:
        await writer.write(line.upper())
```

### Pros

✔ Non-blocking I/O
✔ Scales to many streams
✔ Network-friendly

### Cons

✘ More complex
✘ Overkill for files
✘ Harder debugging

### When to use

* Web servers
* WebSockets
* Kafka / Redis streams
* High-throughput pipelines

---

## D. Side-by-side summary

| Approach      | Best Use Case  | Complexity | Speed     |
| ------------- | -------------- | ---------- | --------- |
| File iterator | CLI tools      | Low        | High      |
| Generator     | Data pipelines | Medium     | High      |
| Async streams | Network I/O    | High       | Very high |

---

## Mental model (important)

* **My current code** = *Unix filter*
* **Generator version** = *functional pipeline*
* **Async version** = *event-driven streaming system*

All three solve the same problem — **flowing data** — at different scales.

---
