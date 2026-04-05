import time
import uuid
import threading
from typing import Dict, Any, Optional

class SessionManager:
    def __init__(self, expiry_seconds: int = 1800):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.expiry_seconds = expiry_seconds
        self._lock = threading.Lock()
        # start a background cleanup thread
        thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        thread.start()

    def create_session(self, data: Dict[str, Any] = None) -> str:
        """Create new session with unique ID"""
        session_id = str(uuid.uuid4())
        now = time.time()
        with self._lock:
            self.sessions[session_id] = {
                'data': data or {},
                'created_at': now,
                'last_accessed': now,
            }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data if not expired"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            session = self.sessions[session_id]
            if time.time() - session['last_accessed'] > self.expiry_seconds:
                # Session expired
                del self.sessions[session_id]
                return None
            session['last_accessed'] = time.time()
            return session['data']

    def save(self, session_id: str, browser: Any):
        """Store or update a browser in session."""
        with self._lock:
            now = time.time()
            self.sessions[session_id] = {
                'data': {'bot': browser},
                'created_at': now,
                'last_accessed': now,
            }

    def delete(self, session_id: str):
        """Remove session"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]

    def cleanup_expired(self):
        """Remove all expired sessions"""
        current_time = time.time()
        with self._lock:
            expired = [sid for sid, sess in self.sessions.items()
                       if current_time - sess['last_accessed'] > self.expiry_seconds]
            for sid in expired:
                del self.sessions[sid]

    def _cleanup_worker(self):
        while True:
            time.sleep(self.expiry_seconds / 2)
            try:
                self.cleanup_expired()
            except Exception:
                pass
