# lmdb-simple

## Project Overview

This document outlines the implementation and packaging plan for the 
`lmdb-simple` Python package, targeting Python 3.9+ and designed to be 
OS-agnostic. The package will provide a dict-like interface on top of 
an LMDB disk store, with context-manager support and fork-safe
multiprocessing readers (picklable LmdbDict instances).

### 1. Project Layout

```plaintext
lmdb-simple/
├── LICENSE
├── MANIFEST.in
├── README.md
├── setup.py
└── lmdb_simple/
    ├── __init__.py
    └── core.py
```

### 2. Dependencies

• `lmdb>=1.0.0`
• Python standard library (`typing`, `pathlib`, `multiprocessing`)

### 3. Core API (`lmdb_simple/core.py`)

- `class LmdbDict[K, V]` (implements `MutableMapping[K, V]` and `ContextManager`)
  • `__init__(self, path: Union[str, Path], writer: bool = False, **env_kwargs)`
  • Mapping methods: `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `__iter__`
  • Views: `keys()`, `values()`, `items()`
  • Sync/flush: `flush()`
  • Close: `close()`
  • Context‐manager: `__enter__()`, `__exit__()`
  • Optional `transaction(write: bool)` context manager for batch writes
  • Full type hints and docstrings on public methods


### 5. Packaging (`setup.py`)

- `name="lmdb-simple"`, `version="0.1.0"`
- `python_requires=">=3.9"`
- `install_requires=["lmdb>=1.0.0"]`
- Read long description from `README.md`
- Include license, classifiers, and `find_packages()`
- `MANIFEST.in` to include `README.md` and `LICENSE`

### 6. Documentation & Examples

- Flesh out `README.md` (this file) with:
  - Quickstart examples for reader/writer, context managers, and multiprocessing
  - API reference links to docstrings

### 7. OS‐Agnostic Considerations

- Use `pathlib` for filesystem paths
- Rely on LMDB’s cross‐platform locking

### 8. Publishing Workflow

1. Build: `python setup.py sdist bdist_wheel`
2. Upload: `twine upload dist/*`
3. Tag & release on GitHub

---

With this plan in place, we can now scaffold and implement the package per 
these outlines.
## Quickstart

Install from PyPI:
```bash
pip install lmdb-simple
```

Basic usage:
```python
from lmdb_simple.core import LmdbDict

# Writer mode: open (and create if needed) for writing
with LmdbDict("path/to/db", writer=True, map_size=10_000_000) as db:
    db["foo"] = "bar"                # store strings
    db[b"bytes"] = b"raw bytes"      # store raw bytes
    db[1] = {"nested": [1, 2, 3]}     # store arbitrary Python objects

# Reader mode: open for read-only
with LmdbDict("path/to/db") as db:
    print(db["foo"])                 # "bar"
    print(db[b"bytes"])              # b"raw bytes"
    print(db[1])                       # {"nested": [1, 2, 3]}
    for key, value in db.items():
        print(key, value)
```

### Multiprocessing

```python
from lmdb_simple.core import LmdbDict
from multiprocessing import Pool

TEST_DB_PATH = "path/to/db"

# Create the reader at module level so that each worker process
# will reuse the same LMDB environment when unpickled.
reader = LmdbDict(TEST_DB_PATH)

def reader_worker(key):
    return reader[key]

if __name__ == "__main__":
    keys = [...]

    with Pool(processes=4) as pool:
        for result in pool.imap_unordered(reader_worker, keys):
            print(result)
```
