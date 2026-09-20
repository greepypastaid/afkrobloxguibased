"""
afk_engine.py
=============
Engine Orchestrator untuk Roblox Universal AFK Bot.
Mengelola threading, status siklus hidup, dan mendelegasikan eksekusi
ke strategi AFK (Auto Fish, Walk & Jump, Clicker, Spammer).
"""

import time
import threading
import ctypes
from typing import Callable, Optional

from core.constants import (
    AFKMode,
    WalkPattern,
    MouseButton,
    EngineState,
    SCAN_CODES,
    VK_CODES
)
from core.config import AFKConfig
from core.win32_api import (
    user32,
    get_open_windows,
    find_roblox_hwnd,
    focus_window,
    is_valid_hwnd
)
from core.controllers import BackgroundController, ForegroundController
from core.strategies import create_strategy, BaseAFKStrategy


class AFKEngine:
    """
    Engine utama yang mengontrol jalannya otomatisasi AFK.
    Menerapkan Separation of Concerns dengan mendelegasikan aksi ke strategy classes.
    """

    # Alias konstanta state untuk backward compatibility
    STATE_STOPPED = EngineState.STOPPED.value
    STATE_COUNTDOWN = EngineState.COUNTDOWN.value
    STATE_RUNNING = EngineState.RUNNING.value

    # Alias mode untuk backward compatibility
    MODE_WALK_JUMP = AFKMode.WALK_JUMP.value
    MODE_AUTO_FISH = AFKMode.AUTO_FISH.value
    MODE_AUTO_CLICKER = AFKMode.AUTO_CLICKER.value
    MODE_KEY_SPAMMER = AFKMode.KEY_SPAMMER.value

    def __init__(self, config: Optional[AFKConfig] = None):
        self.config: AFKConfig = config or AFKConfig()
        self.fg_controller = ForegroundController()
        self.bg_controller = BackgroundController()

        self.state: EngineState = EngineState.STOPPED
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Statistik
        self.start_time: float = 0.0
        self.primary_count: int = 0
        self.secondary_count: int = 0

        # Callback untuk integrasi UI / Logging
        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_stats_update: Optional[Callable[[float, int, int], None]] = None

    @property
    def stop_requested(self) -> bool:
        """Cek apakah sinyal stop telah dikirim."""
        return self._stop_event.is_set()

    def log(self, message: str) -> None:
        """Mengirim pesan log ke callback atau mencetak ke console dengan aman."""
        if self.on_log:
            try:
                self.on_log(message)
            except Exception:
                pass
        else:
            try:
                print(f"[AFK] {message}")
            except UnicodeEncodeError:
                safe_msg = message.encode("ascii", errors="replace").decode("ascii")
                print(f"[AFK] {safe_msg}")

    def set_state(self, new_state: EngineState) -> None:
        """Memperbarui status engine dan memicu callback."""
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(new_state.value)

    def is_running(self) -> bool:
        """Cek apakah engine sedang dalam proses berjalan atau countdown."""
        return self.state in (EngineState.RUNNING, EngineState.COUNTDOWN)

    def start(self) -> None:
        """Memulai loop otomatisasi di background thread."""
        if self.is_running():
            return

        self._stop_event.clear()
        self.start_time = time.time()
        self.primary_count = 0
        self.secondary_count = 0

        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        """Menghentikan bot dan melepaskan seluruh tombol."""
        if not self.is_running():
            return

        self._stop_event.set()
        self.fg_controller.release_all()
        self.set_state(EngineState.STOPPED)
        self.log("Bot dihentikan. Semua tombol dilepaskan.")

    def sleep_interruptible(self, seconds: float) -> bool:
        """
        Sleep yang dapat diinterupsi seketika saat stop() dipanggil.
        Mengembalikan True jika waktu selesai normal, False jika stop diminta.
        """
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self.stop_requested:
                return False
            time.sleep(0.04)
            if self.on_stats_update and self.state == EngineState.RUNNING:
                elapsed = time.time() - self.start_time
                self.on_stats_update(elapsed, self.primary_count, self.secondary_count)
        return True

    def resolve_target_hwnd(self) -> Optional[int]:
        """Menentukan handle jendela target yang valid."""
        hwnd = self.config.target_hwnd
        if is_valid_hwnd(hwnd):
            return hwnd

        # Prioritaskan pencarian jendela Roblox otomatis
        roblox_hwnd = find_roblox_hwnd()
        if roblox_hwnd and is_valid_hwnd(roblox_hwnd):
            self.config.target_hwnd = roblox_hwnd
            return roblox_hwnd

        # Pencarian berdasarkan judul kustom
        if self.config.target_title:
            for h, title in get_open_windows():
                if self.config.target_title.lower() in title.lower():
                    self.config.target_hwnd = h
                    return h

        return None

    def _run_worker(self) -> None:
        """Siklus hidup thread eksekusi utama."""
        try:
            target_hwnd = self.resolve_target_hwnd()

            # 1. Penanganan Jendela & Mode
            if self.config.background_mode:
                if target_hwnd:
                    buff = ctypes.create_unicode_buffer(256)
                    user32.GetWindowTextW(target_hwnd, buff, 256)
                    self.log(f"Target Background: [{target_hwnd}] {buff.value}")
                else:
                    self.log("Jendela target belum terdeteksi. Mencari game di latar belakang...")
            else:
                if target_hwnd:
                    focus_window(target_hwnd)
                    self.log(f"Memfokuskan jendela: HWND {target_hwnd}")

            # 2. Hitung Mundur
            if self.config.countdown_sec > 0:
                self.set_state(EngineState.COUNTDOWN)
                for sec in range(self.config.countdown_sec, 0, -1):
                    if self.stop_requested:
                        return
                    self.log(f"Bersiap mulai dalam {sec} detik...")
                    time.sleep(1.0)

            if self.stop_requested:
                return

            self.set_state(EngineState.RUNNING)
            mode_enum = self.config.mode if isinstance(self.config.mode, AFKMode) else AFKMode(self.config.mode)
            self.log(f"Bot aktif di mode: {mode_enum.name}")

            # 3. Eksekusi Strategi Terpilih (Strategy Pattern)
            strategy: BaseAFKStrategy = create_strategy(mode_enum)
            while not self.stop_requested:
                should_continue = strategy.run_cycle(self, target_hwnd)
                if not should_continue:
                    break

        except Exception as e:
            self.log(f"Kesalahan: {str(e)}")
        finally:
            self.fg_controller.release_all()
            self.set_state(EngineState.STOPPED)



# Re-exports untuk kemudahan impor langsung dari afk_engine
__all__ = [
    "AFKEngine",
    "AFKConfig",
    "AFKMode",
    "WalkPattern",
    "MouseButton",
    "EngineState",
    "get_open_windows",
    "find_roblox_hwnd",
    "focus_window",
    "is_valid_hwnd"
]
