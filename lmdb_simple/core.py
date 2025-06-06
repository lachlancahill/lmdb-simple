from __future__ import annotations
import lmdb
from pathlib import Path
from typing import (
    Generic,
    TypeVar,
    Iterator,
    Union,
    Optional,
    MutableMapping,
    Any,
    ContextManager,
)

K = TypeVar("K")
V = TypeVar("V")

class LmdbDict(MutableMapping[K, V], ContextManager[LmdbDict[K, V]], Generic[K, V]):
    """
    LMDB-backed dict-like store.

    Example:
        with LmdbDict("data.mdb", writer=True) as db:
            db[b"key"] = b"value"
        with LmdbDict("data.mdb") as db:
            print(db[b"key"])
    """
    def __init__(
        self,
        path: Union[str, Path],
        writer: bool = False,
        **env_kwargs: Any,
    ) -> None:
        self.path = Path(path)
        self.writer = writer
        # Ensure environment directory exists when writing
        if self.writer:
            self.path.mkdir(parents=True, exist_ok=True)
        self.env_kwargs = env_kwargs
        self.env: Optional[lmdb.Environment] = None
        self._open_env()

    def _open_env(self) -> None:
        """Open the LMDB environment."""
        self.env = lmdb.open(
            str(self.path),
            readonly=not self.writer,
            create=self.writer,
            **self.env_kwargs,
        )

    def __getitem__(self, key: K) -> V:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            value = txn.get(key)  # type: ignore
        if value is None:
            raise KeyError(key)  # type: ignore
        return value  # type: ignore

    def __setitem__(self, key: K, value: V) -> None:
        if not self.writer or self.env is None:
            raise RuntimeError("Database not opened for writing")
        with self.env.begin(write=True) as txn:
            txn.put(key, value)  # type: ignore

    def __delitem__(self, key: K) -> None:
        if not self.writer or self.env is None:
            raise RuntimeError("Database not opened for writing")
        with self.env.begin(write=True) as txn:
            success = txn.delete(key)  # type: ignore
        if not success:
            raise KeyError(key)

    def __iter__(self) -> Iterator[K]:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            cursor = txn.cursor()
            for k, _ in cursor:
                yield k  # type: ignore

    def __len__(self) -> int:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            stat = txn.stat()
        return stat["entries"]  # type: ignore

    def keys(self) -> Iterator[K]:
        return self.__iter__()

    def values(self) -> Iterator[V]:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            cursor = txn.cursor()
            for _, v in cursor:
                yield v  # type: ignore

    def items(self) -> Iterator[tuple[K, V]]:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            cursor = txn.cursor()
            for k, v in cursor:
                yield k, v  # type: ignore

    def flush(self) -> None:
        """Force sync to disk."""
        if self.env is None:
            return
        self.env.sync()

    def close(self) -> None:
        """Close the environment."""
        if self.env is not None:
            self.env.close()
            self.env = None

    def __enter__(self) -> LmdbDict[K, V]:
        if self.env is None:
            self._open_env()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        self.close()

    def transaction(self, write: bool = False) -> ContextManager[Any]:
        """
        Context manager for explicit transactions.
        Example:
            with db.transaction(write=True) as txn:
                txn.put(k, v)
        """
        if self.env is None:
            raise RuntimeError("Environment is not open")
        return self.env.begin(write=write)