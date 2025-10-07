
from __future__ import annotations
import threading, time, queue, datetime as dt, re
import sqlite3
from typing import Optional

# Simplified RD Client for current build
class RDClient:
    def __init__(self, token: str):
        self.token = token
    
    def add_magnet(self, magnet: str):
        """Add magnet link to Real-Debrid"""
        # TODO: Implement actual RD API call
        pass
    
    def add_torrent(self, path: str):
        """Add torrent file to Real-Debrid"""
        # TODO: Implement actual RD API call
        pass

class RDError(Exception):
    pass

# Simple Job Store using SQLite
class JobStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rd_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                meta TEXT,
                status TEXT DEFAULT 'queued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def add(self, kind: str, payload: str, meta: dict):
        cursor = self.conn.execute(
            "INSERT INTO rd_queue (kind, payload, meta) VALUES (?, ?, ?)",
            (kind, payload, str(meta))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def fetch(self, status: str, limit: int):
        cursor = self.conn.execute(
            "SELECT id, kind, payload, meta FROM rd_queue WHERE status = ? LIMIT ?",
            (status, limit)
        )
        return [{"id": row[0], "kind": row[1], "payload": row[2], "meta": row[3]} 
                for row in cursor.fetchall()]
    
    def update(self, job_id: int, status: str):
        self.conn.execute(
            "UPDATE rd_queue SET status = ? WHERE id = ?",
            (status, job_id)
        )
        self.conn.commit()

class RDManager:
    # instant_mode: 'instant-only'|'instant-preferred'|'profile-only'
    def __init__(self, db_path: str="queue.db"):
        self.instant_mode = 'profile-only'
        self.store = JobStore(db_path)
        self.stop_event = threading.Event()
        self.thread = None
        self.quiet_hours = None  # (start_hour, end_hour) local time
        self.active_jobs = {}

    def set_quiet_hours(self, start: Optional[int], end: Optional[int]):
        self.quiet_hours = (start, end) if start is not None and end is not None else None

    def within_quiet(self) -> bool:
        if not self.quiet_hours: return False
        sh, eh = self.quiet_hours
        now = dt.datetime.now().hour
        if sh <= eh:
            return sh <= now < eh
        return now >= sh or now < eh

    def start(self, token: str):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, args=(token,), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread: self.thread.join(timeout=2)

    def enqueue_magnet(self, magnet: str, meta=None):
        return self.store.add("magnet", magnet, meta or {})

    def enqueue_torrent(self, path: str, meta=None):
        return self.store.add("torrent", path, meta or {})

    def _run(self, token: str):
        client = RDClient(token=token)
        while not self.stop_event.is_set():
            if self.within_quiet():
                time.sleep(1.0); continue
            batch = self.store.fetch(status="queued", limit=5)
            if not batch:
                time.sleep(0.2); continue
            # simple priority: magnets first
            batch = sorted(batch, key=lambda j: 0 if j['kind']=='magnet' else 1)
            for job in batch:
                if self.stop_event.is_set(): break
                self.store.update(job["id"], status="running")
                try:
                    if job["kind"] == "magnet":
                        client.add_magnet(job["payload"])
                    else:
                        client.add_torrent(job["payload"])
                    self.store.update(job["id"], status="done")
                except RDError as e:
                    self.store.update(job["id"], status="failed", meta={"error": str(e)})
            time.sleep(0.1)


def snapshot_db(self, outdir: str = "logs/snapshots"):
    import shutil, os, time
    os.makedirs(outdir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(self.store.db_path, os.path.join(outdir, f"queue-{ts}.sqlite3"))
    return os.path.join(outdir, f"queue-{ts}.sqlite3")


def poll_info_and_select(self, client: RDClient, torrent_id: str, indices: str="all"):
    # Placeholder: in real flow, poll /torrents/info/{id} until files ready, then select
    try:
        _ = client.info(torrent_id)  # not parsed here
    except Exception:
        return False
    try:
        client.select_files(torrent_id, indices)
    except Exception:
        pass
    return True


def cached_indices_from_instant(client, info_hash: str) -> set[int]:
    # Shape varies; common: {hash: {"rd": {"<host>": {"filename": "...", "files": ["1","2"]}}}}
    try:
        data = client.instant(info_hash) or {}
    except Exception:
        return set()
    ids = set()
    # Try common patterns
    def collect(v):
        if isinstance(v, dict):
            for k2, v2 in v.items():
                collect(v2)
        elif isinstance(v, list):
            for x in v:
                try:
                    ids.add(int(x))
                except Exception:
                    pass
    for v in (data.values() if isinstance(data, dict) else []):
        collect(v)
    return ids


import threading, time, math

class DownloadEngine:
    def __init__(self, store, info_size_cache: dict[str,int] | None=None):
        self.store = store
        self.info_size_cache = info_size_cache or {}
        self._threads = []
        self._stop = threading.Event()
        self._pause_ids = set()
        self._cancel_ids = set()
        self.concurrency = 3
        self.bandwidth_kbps = 0  # 0 = unlimited
        self._lock = threading.Lock()
        self._progress = {}  # id -> (done_bytes, total_bytes, started_ts)

    def set_limits(self, concurrency: int, bandwidth_kbps: int):
        with self._lock:
            self.concurrency = max(1, int(concurrency))
            self.bandwidth_kbps = max(0, int(bandwidth_kbps))

    def start(self):
        self._stop.clear()
        self._threads = [threading.Thread(target=self._worker, daemon=True) for _ in range(self.concurrency)]
        for t in self._threads: t.start()

    def stop(self):
        self._stop.set()

    def pause(self, job_id: int): 
        with self._lock: self._pause_ids.add(job_id)
        self.store.update(job_id, status="paused")

    def resume(self, job_id: int):
        with self._lock:
            if job_id in self._pause_ids: self._pause_ids.remove(job_id)
        self.store.update(job_id, status="queued")

    def cancel(self, job_id: int):
        with self._lock: self._cancel_ids.add(job_id)
        self.store.update(job_id, status="cancelled")

    def progress(self, job_id: int):
        with self._lock:
            return self._progress.get(job_id, (0, self.info_size_cache.get(str(job_id), 0), 0))

    def _worker(self):
        while not self._stop.is_set():
            # fetch a queued job
            batch = self.store.fetch(status="queued", limit=1)
            if not batch:
                time.sleep(0.2); continue
            job = batch[0]
            jid = job["id"]
            if jid in self._cancel_ids:
                self.store.update(jid, status="cancelled"); continue
            if jid in self._pause_ids:
                time.sleep(0.2); continue
            # mark running
            self.store.update(jid, status="running")
            total = self.info_size_cache.get(str(jid), 100*1024*1024)  # default 100MB if unknown
            with self._lock:
                self._progress[jid] = (0, total, time.time())
            # simulate download: increase done respecting global bandwidth cap
            while not self._stop.is_set():
                with self._lock:
                    if jid in self._cancel_ids:
                        self.store.update(jid, status="cancelled"); break
                    if jid in self._pause_ids:
                        time.sleep(0.2); continue
                    done, total, started = self._progress[jid]
                    # chunk size per tick based on bandwidth cap
                    if self.bandwidth_kbps > 0:
                        per_sec = self.bandwidth_kbps * 1024
                        chunk = max(16*1024, per_sec // max(1, self.concurrency) // 5)  # 5 ticks per sec
                    else:
                        chunk = 2*1024*1024
                    done = min(total, done + chunk)
                    self._progress[jid] = (done, total, started)
                if done >= total:
                    self.store.update(jid, status="done")
                    break
                time.sleep(0.2)

class RDManager:
    def __init__(self, db_path: str="queue.db"):
        self.instant_mode = 'profile-only'
        from app.queue.store import JobStore
        self.store = JobStore(db_path)
        self.stop_event = threading.Event()
        self.info_size_cache = {}  # str(job_id) -> size bytes
        self.engine = DownloadEngine(self.store, self.info_size_cache)

    def snapshot_db(self, outdir: str = "logs/snapshots"):
        import shutil, os, time
        os.makedirs(outdir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        shutil.copyfile(self.store.db_path, os.path.join(outdir, f"queue-{ts}.sqlite3"))
        return os.path.join(outdir, f"queue-{ts}.sqlite3")

    def start_workers(self, concurrency: int, bandwidth_kbps: int):
        self.engine.set_limits(concurrency, bandwidth_kbps)
        self.engine.start()

    def stop_workers(self):
        self.engine.stop()

    def pause_job(self, job_id: int): self.engine.pause(job_id)
    def resume_job(self, job_id: int): self.engine.resume(job_id)
    def cancel_job(self, job_id: int): self.engine.cancel(job_id)

    def job_progress(self, job_id: int):
        return self.engine.progress(job_id)


def verify_checksum(path: str, expected: str) -> bool:
    import hashlib, os
    algo, _, val = expected.partition(":")
    algo = algo.lower().strip()
    val = val.lower().strip()
    if not os.path.isfile(path) or not algo or not val:
        return False
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest().lower() == val

# Alias for backward compatibility
RDQueueManager = RDManager
