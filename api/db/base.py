import os
import queue
import threading
from typing import Dict, List, Optional, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.normpath(os.path.join(current_dir, ".."))
load_dotenv(dotenv_path=os.path.join(backend_dir, ".env"))

# -----------------------------------------------------------------------------
# Database Client and WriteQueue
# -----------------------------------------------------------------------------

class DatabaseClient:
    """Mongo client wrapper supporting class-wise (9/10) DB segregation."""

    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")

        db9_name = os.getenv("MONGODB_DB_CLASS9")
        db10_name = os.getenv("MONGODB_DB_CLASS10")

        if not db9_name or not db10_name:
            raise ValueError(
                "Database names for both classes must be set. "
                "Please define MONGODB_DB_CLASS9 and MONGODB_DB_CLASS10 in your environment."
            )

        self._client = MongoClient(uri)
        self._db9 = self._client[db9_name]
        self._db10 = self._client[db10_name]

    def get_collection(
        self,
        name: str,
        is_class10: Optional[bool] = None,
        standard: Optional[int] = None
    ) -> Collection:
        if is_class10 is not None:
            return (self._db10 if is_class10 else self._db9)[name]
        if standard is not None:
            return (self._db10 if int(standard) == 10 else self._db9)[name]
        # default to class 9 if ambiguous
        return self._db9[name]


class WriteQueue:
    """Threaded 'no-wait' write queue for fire-and-forget operations."""

    def __init__(self, db_client: DatabaseClient, worker_count: int = 1) -> None:
        self.db_client = db_client
        self._sync_mode = os.getenv("SERVERLESS", "0") == "1"
        self._q: "queue.Queue[Tuple[str, Tuple, Dict]]" = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        if self._sync_mode:
            return
        for i in range(worker_count):
            t = threading.Thread(target=self._worker, name=f"WriteQueueWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def enqueue(self, op_name: str, *args, **kwargs) -> None:
        """Enqueue an operation by name and args; repository methods will interpret."""
        if self._sync_mode:
            func = kwargs.pop("callable", None)
            if callable(func):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"[WriteQueue] Error processing op {op_name}: {e}")
            return
        self._q.put((op_name, args, kwargs))

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                op_name, args, kwargs = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                # Dispatch via a callable if provided.
                func = kwargs.pop("callable", None)
                if callable(func):
                    func(*args, **kwargs)
            except Exception as e:
                print(f"[WriteQueue] Error processing op {op_name}: {e}")
            finally:
                self._q.task_done()

    def stop(self) -> None:
        if self._sync_mode:
            return
        self._stop_event.set()
        for t in self._workers:
            t.join(timeout=1.0)

