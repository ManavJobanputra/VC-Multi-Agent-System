import logging
import threading
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)


class SelfPingScheduler:
    """Periodically pings a URL (intended: this app's own public /health
    endpoint) to stop free-tier hosts from spinning the app down after a
    period of no external traffic. Runs in a daemon thread so it never
    blocks request handling or app shutdown."""

    def __init__(self, url: str, interval_minutes: int, enabled: bool = True):
        self.url = url
        self.interval_seconds = max(interval_minutes, 1) * 60
        self._enabled = enabled
        self._stop_event = threading.Event()
        self._thread = None

        self.last_ping_at = None
        self.last_ping_status = None
        self.next_ping_at = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[SelfPing] Scheduler started: {self.url} every {self.interval_seconds // 60} min (enabled={self._enabled})")

    def stop(self):
        self._stop_event.set()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        logger.info(f"[SelfPing] {'Enabled' if enabled else 'Disabled'}")

    def is_enabled(self) -> bool:
        return self._enabled

    def status(self) -> dict:
        return {
            "enabled": self._enabled,
            "interval_minutes": self.interval_seconds // 60,
            "url": self.url,
            "last_ping_at": self.last_ping_at.isoformat() if self.last_ping_at else None,
            "last_ping_status": self.last_ping_status,
            "next_ping_at": self.next_ping_at.isoformat() if self.next_ping_at else None,
        }

    def _run(self):
        while not self._stop_event.is_set():
            self.next_ping_at = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)
            interrupted = self._stop_event.wait(self.interval_seconds)
            if interrupted:
                break
            if self._enabled:
                self._ping()

    def _ping(self):
        try:
            resp = requests.get(self.url, timeout=10)
            self.last_ping_status = resp.status_code
            logger.info(f"[SelfPing] {self.url} -> {resp.status_code}")
        except Exception as e:
            self.last_ping_status = f"error: {e}"
            logger.warning(f"[SelfPing] Ping failed: {e}")
        finally:
            self.last_ping_at = datetime.now(timezone.utc)
