"""
core.strategies
===============
Penerapan Strategy Pattern untuk setiap mode AFK.
Log pesan bersih tanpa karakter rusak/emoji, ramah terhadap sistem operasi Windows.
"""

import time
import random
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from .constants import AFKMode, WalkPattern, MouseButton
from .win32_api import is_valid_hwnd

if TYPE_CHECKING:
    from afk_engine import AFKEngine


class BaseAFKStrategy(ABC):
    """Kelas dasar abstrak untuk semua strategi AFK."""

    @abstractmethod
    def run_cycle(self, engine: "AFKEngine", hwnd: Optional[int]) -> bool:
        """
        Mengeksekusi satu siklus perulangan bot.
        Mengembalikan True jika ingin melanjutkan, False jika loop harus berhenti.
        """
        pass


class AutoFishStrategy(BaseAFKStrategy):
    """Strategi otomatisasi memancing."""

    def __init__(self):
        self._cycle = 0

    def run_cycle(self, engine: "AFKEngine", hwnd: Optional[int]) -> bool:
        cfg = engine.config

        # 0. Verifikasi Target HWND jika dalam Background Mode
        if cfg.background_mode:
            if not hwnd or not is_valid_hwnd(hwnd):
                hwnd = engine.resolve_target_hwnd()
            if not hwnd or not is_valid_hwnd(hwnd):
                engine.log("Jendela Roblox tidak terdeteksi. Menunggu game...")
                return engine.sleep_interruptible(2.5)

        self._cycle += 1
        engine.log(f"[Siklus #{self._cycle}] Melempar joran...")

        # 1. Lempar joran
        cast_hold = max(0.1, cfg.fish_cast_duration)
        if cfg.background_mode:
            engine.bg_controller.click(hwnd, button=MouseButton.LEFT, hold_time=cast_hold)
        else:
            engine.fg_controller.click(MouseButton.LEFT)

        # 2. Tunggu ikan makan
        wait_time = max(0.5, cfg.fish_wait_bite)
        if cfg.randomize_interval:
            wait_time *= random.uniform(0.9, 1.15)
        engine.log(f"Menunggu ikan menyambar ({wait_time:.1f}s)...")
        if not engine.sleep_interruptible(wait_time):
            return False

        # 3. Tarik ikan
        reel_duration = max(1.0, cfg.fish_reel_duration)
        reel_speed = max(0.05, cfg.fish_reel_speed)
        engine.log(f"Menarik ikan ({reel_duration:.1f}s)...")

        reel_end = time.time() + reel_duration
        while time.time() < reel_end:
            if engine.stop_requested:
                return False

            if cfg.background_mode:
                engine.bg_controller.click(hwnd, button=MouseButton.LEFT, hold_time=0.03)
                if cfg.fish_tap_space:
                    engine.bg_controller.key_press(hwnd, "space", hold_time=0.03)
            else:
                engine.fg_controller.click(MouseButton.LEFT)
                if cfg.fish_tap_space:
                    engine.fg_controller.press_key("space")
                    time.sleep(0.03)
                    engine.fg_controller.release_key("space")

            engine.secondary_count += 1
            time.sleep(reel_speed)

        engine.primary_count += 1
        engine.log(f"Ikan berhasil ditarik. (Total: {engine.primary_count})")

        # 4. Jeda setelah tangkapan
        post_delay = max(0.5, cfg.fish_post_delay)
        return engine.sleep_interruptible(post_delay)


class WalkJumpStrategy(BaseAFKStrategy):
    """Strategi berjalan dan melompat aman untuk anti-disconnect 20 menit."""

    def run_cycle(self, engine: "AFKEngine", hwnd: Optional[int]) -> bool:
        cfg = engine.config

        # 0. Verifikasi Target HWND jika dalam Background Mode
        if cfg.background_mode:
            if not hwnd or not is_valid_hwnd(hwnd):
                hwnd = engine.resolve_target_hwnd()
            if not hwnd or not is_valid_hwnd(hwnd):
                engine.log("Jendela Roblox tidak terdeteksi. Menunggu game...")
                return engine.sleep_interruptible(2.5)

        base_interval = max(1.0, cfg.walk_interval)
        actual_interval = base_interval * (random.uniform(0.8, 1.2) if cfg.randomize_interval else 1.0)

        # Jalankan aksi pergerakan
        if cfg.background_mode:
            self._walk_background(engine, hwnd, cfg.pattern, cfg.walk_duration)
        else:
            self._walk_foreground(engine, cfg.pattern, cfg.walk_duration)

        # Lompatan berkala
        if cfg.jump_chance > 0 and random.randint(1, 100) <= cfg.jump_chance:
            time.sleep(0.15)
            engine.log("Melompat (Space)...")
            if cfg.background_mode:
                # Pulse sejenak (0.04s) agar 3D motor DirectX Roblox mengeksekusi lompatan
                engine.bg_controller.pulse_to_window(
                    hwnd,
                    lambda: (engine.fg_controller.press_key("space"), time.sleep(0.04), engine.fg_controller.release_key("space")),
                    pulse_time=0.04
                )
                engine.bg_controller.key_press(hwnd, "space", hold_time=0.03)
            else:
                engine.fg_controller.press_key("space")
                time.sleep(0.12)
                engine.fg_controller.release_key("space")
            engine.secondary_count += 1

        engine.log(f"Menunggu {actual_interval:.1f}s sebelum langkah berikutnya...")
        return engine.sleep_interruptible(actual_interval)

    def _walk_foreground(self, engine: "AFKEngine", pattern: WalkPattern, duration: float):
        if pattern == WalkPattern.PING_PONG:
            engine.log(f"Melangkah Maju (W) selama {duration:.2f}s...")
            engine.fg_controller.press_key('w')
            engine.sleep_interruptible(duration)
            engine.fg_controller.release_key('w')
            engine.primary_count += 1

            if not engine.sleep_interruptible(0.25):
                return

            engine.log(f"Melangkah Mundur (S) selama {duration:.2f}s...")
            engine.fg_controller.press_key('s')
            engine.sleep_interruptible(duration)
            engine.fg_controller.release_key('s')
            engine.primary_count += 1

        elif pattern == WalkPattern.SQUARE:
            steps = [('w', "Maju"), ('d', "Kanan"), ('s', "Mundur"), ('a', "Kiri")]
            for k, label in steps:
                engine.log(f"Melangkah {label} ({k.upper()})...")
                engine.fg_controller.press_key(k)
                engine.sleep_interruptible(duration * 0.75)
                engine.fg_controller.release_key(k)
                engine.primary_count += 1
                if not engine.sleep_interruptible(0.2):
                    return
        elif pattern == WalkPattern.LEFT_RIGHT:
            steps = [('a', "Kiri"), ('d', "Kanan")]
            for k, label in steps:
                engine.log(f"Melangkah {label} ({k.upper()})...")
                engine.fg_controller.press_key(k)
                engine.sleep_interruptible(duration)
                engine.fg_controller.release_key(k)
                engine.primary_count += 1
                if not engine.sleep_interruptible(0.25):
                    return
        else:
            k, label = random.choice([('w', "Maju"), ('s', "Mundur"), ('a', "Kiri"), ('d', "Kanan")])
            engine.log(f"Melangkah {label} ({k.upper()})...")
            engine.fg_controller.press_key(k)
            engine.sleep_interruptible(duration)
            engine.fg_controller.release_key(k)
            engine.primary_count += 1

    def _walk_background(self, engine: "AFKEngine", hwnd: int, pattern: WalkPattern, duration: float):
        """
        Pergerakan Background aman & tanpa mencuri fokus kerja pengguna.
        Mengirim rotasi kamera Anti-AFK senyap, dan pulse micro-step 0.04s.
        """
        # 1. Reset timer 20 menit idle Roblox secara senyap
        engine.bg_controller.anti_afk_nudge(hwnd)

        # 2. Tentukan urutan tombol langkah
        if pattern == WalkPattern.PING_PONG:
            keys = ['w', 's']
        elif pattern == WalkPattern.SQUARE:
            keys = ['w', 'd', 's', 'a']
        elif pattern == WalkPattern.LEFT_RIGHT:
            keys = ['a', 'd']
        else:
            keys = [random.choice(['w', 's', 'a', 'd'])]

        # 3. Jalankan micro-step via pulse cepat
        for k in keys:
            if engine.stop_requested:
                return
            engine.log(f"Langkah Background ({k.upper()})...")
            engine.bg_controller.key_press(hwnd, k, hold_time=0.04)
            engine.bg_controller.pulse_to_window(
                hwnd,
                lambda key=k: (engine.fg_controller.press_key(key), time.sleep(0.04), engine.fg_controller.release_key(key)),
                pulse_time=0.04
            )
            engine.primary_count += 1
            if len(keys) > 1 and not engine.sleep_interruptible(0.25):
                return


class AutoClickerStrategy(BaseAFKStrategy):
    """Strategi Auto Clicker berulang."""

    def run_cycle(self, engine: "AFKEngine", hwnd: Optional[int]) -> bool:
        cfg = engine.config
        btn = cfg.clicker_button
        interval = max(0.02, cfg.clicker_interval)

        if cfg.background_mode:
            if not hwnd or not is_valid_hwnd(hwnd):
                hwnd = engine.resolve_target_hwnd()
            if not hwnd or not is_valid_hwnd(hwnd):
                engine.log("Jendela Roblox tidak terdeteksi. Menunggu game...")
                return engine.sleep_interruptible(2.5)
            engine.bg_controller.click(hwnd, button=btn, hold_time=0.03)
        else:
            engine.fg_controller.click(button=btn)

        engine.primary_count += 1
        return engine.sleep_interruptible(interval)


class KeySpammerStrategy(BaseAFKStrategy):
    """Strategi penekanan tombol berulang (misal: 'E', 'F', 'Space')."""

    def run_cycle(self, engine: "AFKEngine", hwnd: Optional[int]) -> bool:
        cfg = engine.config
        key = cfg.spam_key.strip().lower()
        interval = max(0.05, cfg.spam_interval)

        if cfg.background_mode:
            if not hwnd or not is_valid_hwnd(hwnd):
                hwnd = engine.resolve_target_hwnd()
            if not hwnd or not is_valid_hwnd(hwnd):
                engine.log("Jendela Roblox tidak terdeteksi. Menunggu game...")
                return engine.sleep_interruptible(2.5)

            engine.bg_controller.key_press(hwnd, key, hold_time=0.04)
            engine.bg_controller.pulse_to_window(
                hwnd,
                lambda: (engine.fg_controller.press_key(key), time.sleep(0.03), engine.fg_controller.release_key(key)),
                pulse_time=0.03
            )
        else:
            engine.fg_controller.press_key(key)
            time.sleep(0.05)
            engine.fg_controller.release_key(key)

        engine.primary_count += 1
        return engine.sleep_interruptible(interval)


def create_strategy(mode: AFKMode) -> BaseAFKStrategy:
    """Factory function untuk menghasilkan strategi berdasarkan mode."""
    strategies = {
        AFKMode.AUTO_FISH: AutoFishStrategy,
        AFKMode.WALK_JUMP: WalkJumpStrategy,
        AFKMode.AUTO_CLICKER: AutoClickerStrategy,
        AFKMode.KEY_SPAMMER: KeySpammerStrategy,
    }
    strategy_cls = strategies.get(mode, AutoFishStrategy)
    return strategy_cls()

