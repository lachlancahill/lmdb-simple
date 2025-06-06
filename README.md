# lmdb-simple

## Project Overview

This document outlines the implementation and packaging plan for the 
`lmdb-simple` Python package, targeting Python 3.9+ and designed to be 
OS-agnostic. The package will provide a dict-like interface on top of 
an LMDB disk store, with context-manager support and a multiprocessing‐
reader helper.

### 1. Project Layout

```
lmdb-simple/
├── LICENSE
├── MANIFEST.in
├── README.md
├── setup.py
└── lmdb_simple/
    ├── __init__.py
    ├── core.py
    └── pool.py
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

### 4. Multiprocessing‐Reader Helper (`lmdb_simple/pool.py`)

Provide a helper for safely using LMDB readers in a `multiprocessing.Pool`:

```python
def make_reader_pool(
    path: Union[str, Path],
    processes: int,
    env_kwargs: Optional[Dict[str, Any]] = None
) -> multiprocessing.Pool:
    """
    Return a Pool whose workers each initialize a module‐level LmdbDict reader.
    """
    ...
```

Internally use `Pool(initializer=..., initargs=(path, env_kwargs))`, with 
a worker‐side `init_reader` that opens `lmdb_simple.core.LmdbDict` in read mode.

### 5. Packaging (`setup.py`)

- `name="lmdb-simple"`, `version="0.1.0"`
- `python_requires=">=3.9"`
- `install_requires=["lmdb>=1.0.0"]`
- Read long description from `README.md`
- Include license, classifiers, and `find_packages()`
- `MANIFEST.in` to include `README.md` and `LICENSE`

### 6. Documentation & Examples

- Flesh out `README.md` (this file) with:
  - Quickstart examples for reader/writer and context managers
  - Multiprocessing‐pool example
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
    db[b"foo"] = b"bar"
    # batch writes via transaction
    with db.transaction(write=True) as txn:
        txn.put(b"hello", b"world")

# Reader mode: open for read-only
with LmdbDict("path/to/db") as db:
    print(db[b"foo"])        # b"bar"
    for key, value in db.items():
        print(key, value)
```

Multiprocessing reader pool:
```python
from lmdb_simple.pool import make_reader_pool, lmdb_reader

def worker(key: bytes) -> bytes:
    # each worker has lmdb_reader initialized
    return lmdb_reader[key]

pool = make_reader_pool("path/to/db", processes=4)
keys = [b"foo", b"hello"]
results = pool.map(worker, keys)
pool.close()
pool.join()
print(results)
```


