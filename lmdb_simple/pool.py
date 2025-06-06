from __future__ import annotations
import multiprocessing
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .core import LmdbDict

# Module‐level reader instance, initialized in worker processes.
lmdb_reader: Optional[LmdbDict[Any, Any]] = None

def init_reader(path: Union[str, Path], env_kwargs: Optional[Dict[str, Any]] = None) -> None:
    """
    Initializer for Pool workers: create a read‐only LmdbDict available as `lmdb_reader`.
    """
    global lmdb_reader
    lmdb_reader = LmdbDict(path, writer=False, **(env_kwargs or {}))

def make_reader_pool(
    path: Union[str, Path],
    processes: int,
    env_kwargs: Optional[Dict[str, Any]] = None,
) -> multiprocessing.Pool:
    """
    Return a multiprocessing.Pool where each worker has a module‐level `lmdb_reader`
    initialized in read‐only mode.

    Usage:
        pool = make_reader_pool("data.mdb", processes=4)
        results = pool.map(worker_fn, iterable)

    Worker functions can access `lmdb_simple.pool.lmdb_reader`.
    """
    return multiprocessing.Pool(
        processes=processes,
        initializer=init_reader,
        initargs=(path, env_kwargs),
    )