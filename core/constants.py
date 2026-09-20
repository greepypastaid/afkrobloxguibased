"""
core.constants
==============
Konstanta dan Enumerasi terpusat untuk aplikasi AFK Bot.
Bersih, profesional, dan bebas dari broken glyph/emoji formatting.
"""

from enum import Enum
from typing import Dict


class AFKMode(str, Enum):
    """Daftar mode otomatisasi AFK yang didukung."""
    AUTO_FISH = "auto_fish"
    WALK_JUMP = "walk_jump"
    AUTO_CLICKER = "auto_clicker"
    KEY_SPAMMER = "key_spammer"

    @classmethod
    def display_name(cls, mode: "AFKMode") -> str:
        names = {
            cls.AUTO_FISH: "Auto Fish",
            cls.WALK_JUMP: "Walk & Jump",
            cls.AUTO_CLICKER: "Auto Clicker",
            cls.KEY_SPAMMER: "Key Spammer"
        }
        return names.get(mode, mode.value)


class WalkPattern(str, Enum):
    """Pola pergerakan karakter 3D."""
    PING_PONG = "ping_pong"
    SQUARE = "square"
    LEFT_RIGHT = "left_right"
    RANDOM = "random"

    @classmethod
    def display_name(cls, pattern: "WalkPattern") -> str:
        names = {
            cls.PING_PONG: "Maju - Mundur",
            cls.SQUARE: "Kotak",
            cls.LEFT_RIGHT: "Kiri - Kanan",
            cls.RANDOM: "Acak"
        }
        return names.get(pattern, pattern.value)


class MouseButton(str, Enum):
    """Pilihan tombol mouse untuk klik."""
    LEFT = "left"
    RIGHT = "right"


class EngineState(str, Enum):
    """Status siklus hidup engine bot."""
    STOPPED = "STOPPED"
    COUNTDOWN = "COUNTDOWN"
    RUNNING = "RUNNING"


# ==========================================
# WINDOWS API MESSAGE CONSTANTS
# ==========================================
WM_KEYDOWN     = 0x0100
WM_KEYUP       = 0x0101
WM_CHAR        = 0x0102
WM_MOUSEMOVE   = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205
MK_LBUTTON     = 0x0001
MK_RBUTTON     = 0x0002


KEYEVENTF_KEYUP    = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_MOUSE        = 0
INPUT_KEYBOARD     = 1


# ==========================================
# HARDWARE SCAN CODES (DIRECTX / DIRECTINPUT)
# ==========================================
SCAN_CODES: Dict[str, int] = {
    'w': 0x11,
    'a': 0x1E,
    's': 0x1F,
    'd': 0x20,
    'space': 0x39,
    'e': 0x12,
    'f': 0x21,
}


# ==========================================
# VIRTUAL KEY CODES (WINDOWS VK)
# ==========================================
VK_CODES: Dict[str, int] = {
    'space': 0x20,
    'e': 0x45,
    'f': 0x46,
    'w': 0x57,
    'a': 0x41,
    's': 0x53,
    'd': 0x44,
    'q': 0x51,
    'r': 0x52,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    'enter': 0x0D,
    'tab': 0x09,
    'shift': 0x10,
    'ctrl': 0x11,
}


# ==========================================
# UI COLOR THEME (CLEAN WHITE / MINIMALIST LIGHT)
# ==========================================
class UIColors:
    BG = "#f8fafc"
    CARD_BG = "#ffffff"
    CARD_BORDER = "#e2e8f0"
    ACCENT_GREEN = "#10b981"
    ACCENT_GREEN_HOVER = "#059669"
    DANGER_RED = "#ef4444"
    DANGER_RED_HOVER = "#dc2626"
    ACCENT_BLUE = "#2563eb"
    TEXT_PRIMARY = "#0f172a"
    TEXT_MUTED = "#64748b"
    INPUT_BG = "#f1f5f9"
    INPUT_BORDER = "#cbd5e1"
