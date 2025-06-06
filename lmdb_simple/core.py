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

import pickle

K = TypeVar("K")
V = TypeVar("V")

# Internal serialization prefixes for raw bytes vs pickled objects
_RAW_PREFIX: bytes = b'\x00'
_PICKLE_PREFIX: bytes = b'\x01'

class LmdbDict(MutableMapping[K, V], ContextManager['LmdbDict[K, V]'], Generic[K, V]):
    """
    LMDB-backed dict-like store with transparent serialization.

    Example:
        with LmdbDict("data.mdb", writer=True) as db:
            db["key"] = "value"
            db[b"raw"] = b"bytes"
            db[1] = {"nested": [1, 2, 3]}
        with LmdbDict("data.mdb") as db:
            print(db["key"])   # "value"
            print(db[b"raw"])   # b"bytes"
            print(db[1])         # {"nested": [1, 2, 3]}
    """
    def _serialize(self, obj: Any) -> bytes:
        """Serialize a Python object to bytes with internal prefix."""
        if isinstance(obj, bytes):
            return _RAW_PREFIX + obj
        return _PICKLE_PREFIX + pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes with internal prefix back to a Python object."""
        tag = data[:1]
        if tag == _RAW_PREFIX:
            return data[1:]
        if tag == _PICKLE_PREFIX:
            return pickle.loads(data[1:])
        return data

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
            # create=self.writer,
            **self.env_kwargs,
        )

    def __getitem__(self, key: K) -> V:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        skey = self._serialize(key)
        with self.env.begin(write=False) as txn:
            raw = txn.get(skey)  # type: ignore
        if raw is None:
            raise KeyError(key)  # type: ignore
        return self._deserialize(raw)  # type: ignore

    def __setitem__(self, key: K, value: V) -> None:
        if not self.writer or self.env is None:
            raise RuntimeError("Database not opened for writing")
        skey = self._serialize(key)
        svalue = self._serialize(value)
        with self.env.begin(write=True) as txn:
            txn.put(skey, svalue)  # type: ignore

    def __delitem__(self, key: K) -> None:
        if not self.writer or self.env is None:
            raise RuntimeError("Database not opened for writing")
        skey = self._serialize(key)
        with self.env.begin(write=True) as txn:
            success = txn.delete(skey)  # type: ignore
        if not success:
            raise KeyError(key)

    def __iter__(self) -> Iterator[K]:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            cursor = txn.cursor()
            for sk, _ in cursor:
                yield self._deserialize(sk)  # type: ignore

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
            for _, sv in cursor:
                yield self._deserialize(sv)  # type: ignore

    def items(self) -> Iterator[tuple[K, V]]:
        if self.env is None:
            raise RuntimeError("Environment is not open")
        with self.env.begin(write=False) as txn:
            cursor = txn.cursor()
            for sk, sv in cursor:
                yield self._deserialize(sk), self._deserialize(sv)  # type: ignore

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