# =========================================
# PYTHON SNIPPETS
# CREATING YOUR OWN DATA STREAM IN PYTHON
# =========================================

from __future__ import annotations
from typing import Callable, TextIO


def processor(reader: TextIO, converter: Callable[[str], str], writer: TextIO) -> int:
    """Stream lines from reader → converter → writer. Returns number of lines processed."""
    
    if not callable(converter):
        raise TypeError("converter must be callable")

    count = 0
    
    for line in reader:
        try:
            writer.write(converter(line))
        except Exception as e:
            raise RuntimeError(f"processor failed on line {count + 1}") from e
    
        count += 1
    writer.flush()
    return count
