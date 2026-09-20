"""
core
====
Package inti untuk Roblox Universal AFK Bot.
Menyediakan modularitas, penanganan Win32 API, controller input, konfigurasi, dan strategi AFK.
"""

from .constants import (
    AFKMode,
    WalkPattern,
    MouseButton,
    EngineState,
    SCAN_CODES,
    VK_CODES,
    UIColors
)
from .config import AFKConfig
from .controllers import BackgroundController, ForegroundController
from .win32_api import (
    get_open_windows,
    find_roblox_hwnd,
    is_roblox_window,
    get_window_client_center,
    focus_window
)


__all__ = [
    "AFKMode",
    "WalkPattern",
    "MouseButton",
    "EngineState",
    "SCAN_CODES",
    "VK_CODES",
    "UIColors",
    "AFKConfig",
    "BackgroundController",
    "ForegroundController",
    "get_open_windows",
    "find_roblox_hwnd",
    "get_window_client_center",
    "focus_window",
]
