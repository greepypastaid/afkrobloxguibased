"""
core.config
===========
Definisi Dataclass untuk konfigurasi bot dan fungsi persistensi JSON.
Menyimpan dan memuat preferensi pengguna secara otomatis.
"""

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any

from .constants import AFKMode, WalkPattern, MouseButton


@dataclass
class AFKConfig:
    """Konfigurasi bot AFK dengan nilai default yang optimal."""

    # Pengaturan Global
    mode: AFKMode = AFKMode.AUTO_FISH
    background_mode: bool = True
    target_hwnd: Optional[int] = None
    target_title: str = ""
    countdown_sec: int = 2

    # Pengaturan Auto Fish ("Fish It" / Fisch)
    fish_cast_duration: float = 0.6     # Lama tahan klik saat melempar joran (s)
    fish_wait_bite: float = 3.2         # Waktu tunggu ikan menyambar umpan (s)
    fish_reel_duration: float = 4.2     # Waktu menarik joran (s)
    fish_reel_speed: float = 0.12       # Jeda antar klik tarikan (s)
    fish_post_delay: float = 1.2        # Jeda setelah tangkapan sebelum lempar lagi (s)
    fish_tap_space: bool = False        # Tekan spasi juga saat menarik joran

    # Pengaturan Walk & Jump (Anti-AFK 3D)
    walk_interval: float = 6.0          # Jeda antar gerakan (s)
    walk_duration: float = 0.8          # Lama tombol WASD ditahan (s)
    pattern: WalkPattern = WalkPattern.PING_PONG
    jump_chance: int = 80               # Peluang melompat (0-100%)
    randomize_interval: bool = True     # Variasi acak +/- 20% agar natural

    # Pengaturan Auto Clicker
    clicker_interval: float = 0.25      # Interval antar klik (s)
    clicker_button: MouseButton = MouseButton.LEFT

    # Pengaturan Key Spammer
    spam_key: str = "e"                 # Tombol yang di-spam (e, f, space, dll)
    spam_interval: float = 0.5          # Interval penekanan tombol (s)

    def to_dict(self) -> Dict[str, Any]:
        """Konversi konfigurasi ke format dictionary serializable."""
        data = asdict(self)
        data["mode"] = self.mode.value if isinstance(self.mode, AFKMode) else self.mode
        data["pattern"] = self.pattern.value if isinstance(self.pattern, WalkPattern) else self.pattern
        data["clicker_button"] = self.clicker_button.value if isinstance(self.clicker_button, MouseButton) else self.clicker_button
        # HWND bersifat dinamis per sesi OS, tidak perlu disimpan
        data.pop("target_hwnd", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AFKConfig":
        """Membuat instance AFKConfig dari dictionary data."""
        clean_data = dict(data)
        if "mode" in clean_data:
            try:
                clean_data["mode"] = AFKMode(clean_data["mode"])
            except ValueError:
                clean_data["mode"] = AFKMode.AUTO_FISH

        if "pattern" in clean_data:
            try:
                clean_data["pattern"] = WalkPattern(clean_data["pattern"])
            except ValueError:
                clean_data["pattern"] = WalkPattern.PING_PONG

        if "clicker_button" in clean_data:
            try:
                clean_data["clicker_button"] = MouseButton(clean_data["clicker_button"])
            except ValueError:
                clean_data["clicker_button"] = MouseButton.LEFT

        # Filter hanya atribut yang ada di dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in clean_data.items() if k in valid_keys}
        return cls(**filtered)

    def save_to_file(self, filepath: Path) -> None:
        """Menyimpan konfigurasi ke file JSON."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception:
            pass

    @classmethod
    def load_from_file(cls, filepath: Path) -> "AFKConfig":
        """Memuat konfigurasi dari file JSON jika ada."""
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls.from_dict(data)
            except Exception:
                pass
        return cls()
