"""
hotkeys.py
----------
Global hotkey management using pynput.
Works even when the application is not in focus.
"""

import threading
from typing import Callable, Optional
from pynput import keyboard as pynput_keyboard


class HotkeyManager:
    """
    Manages global keyboard hotkeys using pynput.
    Runs listener in a background thread.
    """

    def __init__(self):
        self._listener: Optional[pynput_keyboard.Listener] = None
        self._hotkey: str = "q"
        self._callback: Optional[Callable] = None
        self._active = False
        self._current_keys: set = set()
        self._lock = threading.Lock()

    def set_hotkey(self, key: str, callback: Callable):
        """
        Set the global hotkey and callback function.

        Args:
            key: Single key string like 'q', 'f1', etc.
            callback: Function to call when hotkey is pressed
        """
        self._hotkey = key.lower()
        self._callback = callback

    def start(self):
        """Start listening for global hotkeys in background thread."""
        if self._active:
            self.stop()

        self._active = True
        self._listener = pynput_keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()
        print(f"[Hotkeys] Global hotkey listener started. Hotkey: {self._hotkey.upper()}")

    def stop(self):
        """Stop the hotkey listener."""
        self._active = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        print("[Hotkeys] Global hotkey listener stopped.")

    def _normalize_key(self, key) -> Optional[str]:
        """Normalize a pynput key to a simple string."""
        try:
            # Regular character key
            return key.char.lower() if key.char else None
        except AttributeError:
            # Special key
            key_name = str(key).replace("Key.", "").lower()
            return key_name

    def _on_press(self, key):
        """Handle key press event."""
        if not self._active or not self._callback:
            return

        normalized = self._normalize_key(key)
        if normalized is None:
            return

        with self._lock:
            self._current_keys.add(normalized)

        if normalized == self._hotkey.lower():
            # Call callback in main thread via Qt signal mechanism
            # We use a thread-safe approach here
            if self._callback:
                try:
                    self._callback()
                except Exception as e:
                    print(f"[Hotkeys] Callback error: {e}")

    def _on_release(self, key):
        """Handle key release event."""
        normalized = self._normalize_key(key)
        if normalized:
            with self._lock:
                self._current_keys.discard(normalized)

    def update_hotkey(self, new_key: str):
        """Change the active hotkey."""
        self._hotkey = new_key.lower()
        print(f"[Hotkeys] Hotkey updated to: {self._hotkey.upper()}")


# Global hotkey manager
_manager: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """Get or create the global hotkey manager."""
    global _manager
    if _manager is None:
        _manager = HotkeyManager()
    return _manager